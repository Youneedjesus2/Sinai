from src.core.db import SessionLocal
from src.schemas.models import AuditEvent, Conversation, Lead, Message


def test_inbound_happy_path_creates_lead_conversation_messages_and_audits(client):
    response = client.post(
        '/leads/inbound',
        json={
            'agency_id': 'agency-123',
            'name': 'Jane Doe',
            'phone': '+15550001',
            'email': 'jane@example.com',
            'source_channel': 'sms',
            'message_body': 'I need an appointment next week',
            'provider_message_id': 'msg-1',
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body['orchestration']['detected_intent'] == 'appointment_request'

    lead_id = body['id']
    conversation_id = body['conversation']['id']

    with SessionLocal() as db:
        lead = db.get(Lead, lead_id)
        conversation = db.get(Conversation, conversation_id)
        messages = db.query(Message).filter(Message.conversation_id == conversation_id).all()
        audits = db.query(AuditEvent).filter(AuditEvent.lead_id == lead_id).all()

    assert lead is not None
    assert conversation is not None
    assert len(messages) == 2
    assert {m.direction.value for m in messages} == {'inbound', 'outbound'}
    assert len(audits) == 5
    assert {a.event_type for a in audits} == {
        'lead_created',
        'conversation_created',
        'inbound_message_received',
        'orchestration_completed',
        'outbound_reply_created',
    }
