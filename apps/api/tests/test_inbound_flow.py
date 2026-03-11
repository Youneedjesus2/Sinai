from unittest.mock import MagicMock, patch

from src.core.db import SessionLocal
from src.schemas.llm import OrchestratorResult
from src.schemas.models import AuditEvent, Conversation, Lead, Message


def _make_openai_mock(result: OrchestratorResult):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.parsed = result
    mock_client.beta.chat.completions.parse.return_value = mock_response
    return mock_client


def test_inbound_happy_path_creates_lead_conversation_messages_and_audits(client):
    appointment_result = OrchestratorResult(
        detected_intent='appointment_request',
        follow_up_needed=True,
        escalation_needed=False,
        suggested_next_reply='I can help schedule that. What day works best?',
    )

    with patch('src.integrations.openai_client.OpenAI', return_value=_make_openai_mock(appointment_result)):
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
