"""Tests for SummaryService and POST /leads/{lead_id}/summary."""

from unittest.mock import patch

import pytest

from src.schemas.llm import SummaryOutput


def _make_summary_output(**overrides) -> SummaryOutput:
    defaults = dict(
        lead_name='Jane Doe',
        requested_service='Companion care',
        location='Austin, TX',
        care_needs='Lead is caring for an aging parent and needs daily companion support.',
        scheduled_time='June 15, 2026 at 10:00 AM',
        unresolved_questions=['What is the hourly rate?'],
        escalation_reasons=[],
        next_steps='Call lead to confirm consultation and discuss care plan.',
    )
    defaults.update(overrides)
    return SummaryOutput(**defaults)


# ---------------------------------------------------------------------------
# 1. Service: generate_summary creates DB record and audit event
# ---------------------------------------------------------------------------

def test_generate_summary_creates_record_and_audit(reset_db):
    from src.core.db import SessionLocal
    from src.repositories.audit_repository import AuditRepository
    from src.services.summary_service import SummaryService
    from src.schemas.models import Lead

    db = SessionLocal()
    try:
        lead = Lead(agency_id='test-agency', source_channel='email')
        db.add(lead)
        db.flush()
        lead_id = lead.id

        with patch('src.services.summary_service.OpenAIClient') as mock_ai:
            mock_ai.return_value.complete_structured.return_value = _make_summary_output()
            summary = SummaryService(db).generate_summary(lead_id)

        assert summary.id is not None
        assert summary.lead_id == lead_id
        assert 'Jane Doe' in summary.summary_text
        assert summary.summary_json['lead_name'] == 'Jane Doe'
        assert summary.summary_json['requested_service'] == 'Companion care'

        events = AuditRepository(db).list_for_lead(lead_id)
        assert any(e.event_type == 'summary_generated' for e in events)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 2. Service: generate_summary raises ValueError for unknown lead
# ---------------------------------------------------------------------------

def test_generate_summary_raises_for_unknown_lead(reset_db):
    from src.core.db import SessionLocal
    from src.services.summary_service import SummaryService

    db = SessionLocal()
    try:
        with pytest.raises(ValueError, match='9999'):
            SummaryService(db).generate_summary(9999)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 3. Service: transcript includes all messages from all conversations
# ---------------------------------------------------------------------------

def test_generate_summary_builds_transcript_from_messages(reset_db):
    from src.core.db import SessionLocal
    from src.repositories.lead_repository import LeadRepository
    from src.repositories.message_repository import MessageRepository
    from src.schemas.models import Lead, MessageDirection
    from src.services.summary_service import SummaryService

    db = SessionLocal()
    try:
        lead = Lead(agency_id='test-agency', source_channel='sms')
        db.add(lead)
        db.flush()
        lead_id = lead.id

        # Create a conversation with one message
        conversation = LeadRepository(db).create_conversation(lead_id)
        MessageRepository(db).create_message(
            conversation_id=conversation.id,
            direction=MessageDirection.inbound,
            channel='sms',
            body='I need help with senior care.',
        )
        db.flush()

        captured: list[str] = []

        def capture_transcript(system_prompt, user_message, response_model):
            captured.append(user_message)
            return _make_summary_output()

        with patch('src.services.summary_service.OpenAIClient') as mock_ai:
            mock_ai.return_value.complete_structured.side_effect = capture_transcript
            SummaryService(db).generate_summary(lead_id)

        assert len(captured) == 1
        assert 'I need help with senior care.' in captured[0]
        assert '[LEAD]' in captured[0]
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 4. Route: POST /leads/{lead_id}/summary returns 200 with summary data
# ---------------------------------------------------------------------------

def test_summary_route_happy_path(client):
    with (
        patch('src.services.intake_service.OrchestratorService') as mock_orch,
        patch('src.services.intake_service.RetrievalService') as mock_ret,
        patch('src.services.summary_service.OpenAIClient') as mock_ai,
    ):
        from src.schemas.llm import OrchestratorResult, RetrievalResult

        mock_ret.return_value.retrieve.return_value = RetrievalResult(
            context_chunks=['some context'],
            confidence_score=0.9,
            sources=[],
            context_found=True,
        )
        mock_orch.process_inbound_message.return_value = OrchestratorResult(
            detected_intent='general_inquiry',
            follow_up_needed=False,
            escalation_needed=False,
            suggested_next_reply='Thank you for reaching out.',
        )
        mock_ai.return_value.complete_structured.return_value = _make_summary_output()

        # Create a lead first
        inbound_resp = client.post('/leads/inbound', json={
            'agency_id': 'test-agency',
            'source_channel': 'email',
            'message_body': 'I need care services.',
        })
        assert inbound_resp.status_code == 200
        lead_id = inbound_resp.json()['id']

        # Generate summary
        resp = client.post(f'/leads/{lead_id}/summary')
        assert resp.status_code == 200
        body = resp.json()
        assert body['lead_id'] == lead_id
        assert 'summary_text' in body
        assert 'summary_json' in body
        assert body['summary_json']['lead_name'] == 'Jane Doe'


# ---------------------------------------------------------------------------
# 5. Route: POST /leads/{lead_id}/summary returns 404 for missing lead
# ---------------------------------------------------------------------------

def test_summary_route_returns_404_for_missing_lead(client):
    resp = client.post('/leads/99999/summary')
    assert resp.status_code == 404
    assert '99999' in resp.json()['detail']
