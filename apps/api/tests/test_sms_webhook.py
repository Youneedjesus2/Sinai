"""Tests for POST /webhooks/sms/inbound."""

from unittest.mock import MagicMock, patch

import pytest

# conftest.py sets env vars and provides client fixture


INBOUND_URL = '/webhooks/sms/inbound'
VERIFICATION_TOKEN = 'test-verification-token'

INBOUND_PAYLOAD = {
    'body': {
        'direction': 'Inbound',
        'id': 'rc-msg-001',
        'from': {'phoneNumber': '+15550001111'},
        'subject': 'Hello, I need care services',
    }
}


def _headers(verification: str = VERIFICATION_TOKEN) -> dict:
    return {'Verification-Token': verification}


def _mock_intake_result(body: str = 'We can help you. Please call us.'):
    lead = MagicMock()
    lead.id = 'lead-1'
    conversation = MagicMock()
    inbound = MagicMock()
    outbound = MagicMock()
    outbound.body = body
    orchestration = MagicMock()
    return lead, conversation, inbound, outbound, orchestration


# ---------------------------------------------------------------------------
# 1. Validation handshake — RingCentral verifies the webhook URL
# ---------------------------------------------------------------------------

def test_validation_handshake_echoes_token(client):
    resp = client.post(
        INBOUND_URL,
        headers={'Validation-Token': 'some-uuid-token'},
        content='',
    )
    assert resp.status_code == 200
    assert resp.headers.get('Validation-Token') == 'some-uuid-token'


# ---------------------------------------------------------------------------
# 2. Wrong Verification-Token → 403
# ---------------------------------------------------------------------------

def test_wrong_verification_token_returns_403(client):
    resp = client.post(
        INBOUND_URL,
        headers={'Verification-Token': 'wrong-token'},
        json=INBOUND_PAYLOAD,
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 3. Outbound direction is silently ignored (200, no intake)
# ---------------------------------------------------------------------------

def test_outbound_direction_ignored(client):
    payload = {
        'body': {
            'direction': 'Outbound',
            'id': 'rc-msg-002',
            'from': {'phoneNumber': '+15550001111'},
            'subject': 'Reply sent',
        }
    }
    with patch('src.api.routes.sms.IntakeService') as mock_intake:
        resp = client.post(INBOUND_URL, headers=_headers(), json=payload)
    assert resp.status_code == 200
    mock_intake.assert_not_called()


# ---------------------------------------------------------------------------
# 4. Duplicate provider_message_id is idempotent (200, no second intake)
# ---------------------------------------------------------------------------

def test_duplicate_message_id_is_skipped(client):
    # The route calls MessageRepository.find_by_provider_id() before intake.
    # We mock it to return None on the first request (new message) and a
    # MagicMock on the second (duplicate) so idempotency kicks in.
    existing_message = MagicMock()
    find_side_effects = [None, existing_message]

    mock_msg_repo = MagicMock()
    mock_msg_repo.return_value.find_by_provider_id.side_effect = find_side_effects

    with (
        patch('src.api.routes.sms.MessageRepository', mock_msg_repo),
        patch('src.api.routes.sms.IntakeService') as mock_intake,
        patch('src.api.routes.sms.RingCentralClient') as mock_rc,
    ):
        mock_intake.return_value.process_inbound_lead.return_value = _mock_intake_result()
        mock_rc.return_value.send_sms.return_value = 'rc-sent-001'

        # First call — processed normally
        resp1 = client.post(INBOUND_URL, headers=_headers(), json=INBOUND_PAYLOAD)
        assert resp1.status_code == 200
        assert mock_intake.return_value.process_inbound_lead.call_count == 1

        # Second call with same provider_message_id — must be skipped
        resp2 = client.post(INBOUND_URL, headers=_headers(), json=INBOUND_PAYLOAD)
        assert resp2.status_code == 200
        # IntakeService should NOT have been called a second time
        assert mock_intake.return_value.process_inbound_lead.call_count == 1


# ---------------------------------------------------------------------------
# 5. Happy path — inbound SMS triggers intake and sends reply
# ---------------------------------------------------------------------------

def test_happy_path_calls_intake_and_sends_sms(client):
    with (
        patch('src.api.routes.sms.IntakeService') as mock_intake,
        patch('src.api.routes.sms.RingCentralClient') as mock_rc,
    ):
        mock_intake.return_value.process_inbound_lead.return_value = _mock_intake_result()
        mock_rc.return_value.send_sms.return_value = 'rc-sent-002'

        resp = client.post(INBOUND_URL, headers=_headers(), json=INBOUND_PAYLOAD)

        assert resp.status_code == 200
        mock_intake.return_value.process_inbound_lead.assert_called_once()
        mock_rc.return_value.send_sms.assert_called_once_with(
            to='+15550001111',
            body='We can help you. Please call us.',
        )


# ---------------------------------------------------------------------------
# 6. send_sms failure logs external_service_failure audit event
# ---------------------------------------------------------------------------

def test_send_sms_failure_audits_external_service_failure(client):
    with (
        patch('src.api.routes.sms.IntakeService') as mock_intake,
        patch('src.api.routes.sms.RingCentralClient') as mock_rc,
        patch('src.api.routes.sms.AuditRepository') as mock_audit,
    ):
        mock_intake.return_value.process_inbound_lead.return_value = _mock_intake_result()
        mock_rc.return_value.send_sms.return_value = None  # simulate failure

        resp = client.post(INBOUND_URL, headers=_headers(), json=INBOUND_PAYLOAD)

        assert resp.status_code == 200
        mock_audit.return_value.create_event.assert_called_once()
        call_kwargs = mock_audit.return_value.create_event.call_args.kwargs
        assert call_kwargs['event_type'] == 'external_service_failure'
        assert call_kwargs['event_payload']['vendor'] == 'ringcentral'
