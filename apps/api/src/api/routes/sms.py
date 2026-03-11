import logging

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.db import get_db
from src.integrations.ringcentral_client import RingCentralClient
from src.repositories.audit_repository import AuditRepository
from src.repositories.message_repository import MessageRepository
from src.schemas.lead import InboundLeadRequest
from src.services.intake_service import IntakeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/webhooks/sms', tags=['sms'])


@router.post('/inbound')
async def inbound_sms(request: Request, db: Session = Depends(get_db)) -> Response:
    settings = get_settings()

    # --- Validation handshake (first call from RingCentral to verify URL) ---
    validation_token = request.headers.get('Validation-Token')
    if validation_token:
        return Response(
            content='',
            status_code=200,
            headers={'Validation-Token': validation_token},
        )

    # --- Verify subsequent calls are from our subscription ---
    verification_token = request.headers.get('Verification-Token')
    if verification_token != settings.ringcentral_webhook_verification_token:
        logger.warning('SMS webhook received invalid Verification-Token')
        return Response(status_code=403)

    # --- Parse notification body ---
    try:
        payload = await request.json()
        msg = payload['body']
    except Exception:
        logger.error('SMS webhook: failed to parse request body')
        return Response(status_code=200)  # Ack to avoid RingCentral retries

    # --- Only process inbound SMS ---
    direction = msg.get('direction', '')
    if direction != 'Inbound':
        logger.debug('SMS webhook: ignoring %s message', direction)
        return Response(status_code=200)

    provider_message_id: str = str(msg.get('id', ''))
    sender_phone: str = msg.get('from', {}).get('phoneNumber', '')
    message_text: str = msg.get('subject', '')

    # --- Idempotency: ignore already-processed messages ---
    if provider_message_id:
        existing = MessageRepository(db).find_by_provider_id(provider_message_id)
        if existing:
            logger.info('SMS webhook: duplicate message ID %s — skipping', provider_message_id)
            return Response(status_code=200)

    # --- Build intake request and process ---
    intake_request = InboundLeadRequest(
        agency_id=settings.default_agency_id,
        phone=sender_phone,
        source_channel='sms',
        message_body=message_text,
        provider_message_id=provider_message_id,
    )

    try:
        lead, _conversation, _inbound, outbound, _orchestration = (
            IntakeService(db).process_inbound_lead(intake_request)
        )
    except Exception:
        logger.exception('SMS webhook: IntakeService failed for message %s', provider_message_id)
        return Response(status_code=200)

    # --- Send outbound reply via RingCentral ---
    rc_msg_id = RingCentralClient().send_sms(to=sender_phone, body=outbound.body)
    if rc_msg_id is None:
        logger.error('SMS webhook: send_sms failed for lead %s', lead.id)
        AuditRepository(db).create_event(
            lead_id=lead.id,
            event_type='external_service_failure',
            event_payload={'vendor': 'ringcentral', 'error': 'send_sms returned None'},
        )
        db.commit()

    return Response(status_code=200)
