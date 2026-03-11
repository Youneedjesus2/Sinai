import logging
import re

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.db import get_db
from src.integrations.sendgrid_client import SendGridClient
from src.repositories.audit_repository import AuditRepository
from src.repositories.message_repository import MessageRepository
from src.schemas.lead import InboundLeadRequest
from src.services.intake_service import IntakeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/webhooks/email', tags=['email'])

REPLY_SUBJECT = 'Re: Your inquiry — Care Team'


def _extract_email(from_header: str) -> str:
    """Extract bare email address from 'Name <email>' or 'email' format."""
    match = re.search(r'<([^>]+)>', from_header)
    return match.group(1).strip() if match else from_header.strip()


def _extract_name(from_header: str) -> str | None:
    """Extract display name from 'Name <email>' format. Returns None if not present."""
    if '<' not in from_header:
        return None
    name = from_header.split('<')[0].strip().strip('"')
    return name if name else None


def _extract_message_id(headers_str: str) -> str:
    """Parse Message-ID from raw email headers block."""
    match = re.search(r'^Message-ID:\s*(.+)$', headers_str, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else ''


@router.post('/inbound')
async def inbound_email(request: Request, db: Session = Depends(get_db)) -> Response:
    settings = get_settings()

    try:
        form = await request.form()
    except Exception:
        logger.error('Email webhook: failed to parse form data')
        return Response(status_code=200)  # Ack to avoid SendGrid retries

    from_header: str = str(form.get('from', ''))
    subject: str = str(form.get('subject', ''))
    message_text: str = str(form.get('text', ''))
    headers_str: str = str(form.get('headers', ''))

    sender_email: str = _extract_email(from_header)
    sender_name: str | None = _extract_name(from_header)
    provider_message_id: str = _extract_message_id(headers_str)

    # --- Idempotency: ignore already-processed messages ---
    if provider_message_id:
        existing = MessageRepository(db).find_by_provider_id(provider_message_id)
        if existing:
            logger.info('Email webhook: duplicate Message-ID %s — skipping', provider_message_id)
            return Response(status_code=200)

    # --- Build intake request and process ---
    intake_request = InboundLeadRequest(
        agency_id=settings.default_agency_id,
        name=sender_name,
        email=sender_email,
        source_channel='email',
        message_body=message_text,
        provider_message_id=provider_message_id,
    )

    try:
        lead, _conversation, _inbound, outbound, _orchestration = (
            IntakeService(db).process_inbound_lead(intake_request)
        )
    except Exception:
        logger.exception('Email webhook: IntakeService failed for message %s', provider_message_id)
        return Response(status_code=200)

    # --- Send outbound reply via SendGrid ---
    sg_client = SendGridClient()
    success = sg_client.send_email(
        to=sender_email,
        from_=sg_client._from_email,
        subject=REPLY_SUBJECT,
        body=outbound.body,
    )
    if not success:
        logger.error('Email webhook: send_email failed for lead %s', lead.id)
        AuditRepository(db).create_event(
            lead_id=lead.id,
            event_type='external_service_failure',
            event_payload={'vendor': 'sendgrid', 'error': 'send_email returned False'},
        )
        db.commit()

    return Response(status_code=200)
