"""Tests for POST /webhooks/email/inbound."""

from unittest.mock import MagicMock, patch

INBOUND_URL = '/webhooks/email/inbound'

# SendGrid Inbound Parse sends multipart/form-data
HEADERS_WITH_MSG_ID = 'Received: from mail.example.com\r\nMessage-ID: <abc123@mail.example.com>\r\nFrom: Jane Doe <jane@example.com>'

INBOUND_FORM = {
    'from': 'Jane Doe <jane@example.com>',
    'subject': 'Inquiry about home care services',
    'text': 'Hello, I would like to learn more about your services.',
    'headers': HEADERS_WITH_MSG_ID,
}


def _mock_intake_result(body: str = 'Thank you for reaching out. We will be in touch shortly.'):
    lead = MagicMock()
    lead.id = 'lead-1'
    conversation = MagicMock()
    inbound = MagicMock()
    outbound = MagicMock()
    outbound.body = body
    orchestration = MagicMock()
    return lead, conversation, inbound, outbound, orchestration


# ---------------------------------------------------------------------------
# 1. Happy path — inbound email triggers intake and sends reply
# ---------------------------------------------------------------------------

def test_happy_path_calls_intake_and_sends_email(client):
    with (
        patch('src.api.routes.email_webhook.IntakeService') as mock_intake,
        patch('src.api.routes.email_webhook.SendGridClient') as mock_sg,
    ):
        mock_intake.return_value.process_inbound_lead.return_value = _mock_intake_result()
        mock_sg.return_value.send_email.return_value = True
        mock_sg.return_value._from_email = 'noreply@careagency.com'

        resp = client.post(INBOUND_URL, data=INBOUND_FORM)

        assert resp.status_code == 200
        mock_intake.return_value.process_inbound_lead.assert_called_once()
        mock_sg.return_value.send_email.assert_called_once_with(
            to='jane@example.com',
            from_='noreply@careagency.com',
            subject='Re: Your inquiry — Care Team',
            body='Thank you for reaching out. We will be in touch shortly.',
        )


# ---------------------------------------------------------------------------
# 2. Duplicate Message-ID is idempotent
# ---------------------------------------------------------------------------

def test_duplicate_message_id_is_skipped(client):
    existing_message = MagicMock()
    find_side_effects = [None, existing_message]

    mock_msg_repo = MagicMock()
    mock_msg_repo.return_value.find_by_provider_id.side_effect = find_side_effects

    with (
        patch('src.api.routes.email_webhook.MessageRepository', mock_msg_repo),
        patch('src.api.routes.email_webhook.IntakeService') as mock_intake,
        patch('src.api.routes.email_webhook.SendGridClient') as mock_sg,
    ):
        mock_intake.return_value.process_inbound_lead.return_value = _mock_intake_result()
        mock_sg.return_value.send_email.return_value = True
        mock_sg.return_value._from_email = 'noreply@careagency.com'

        # First call — processed
        resp1 = client.post(INBOUND_URL, data=INBOUND_FORM)
        assert resp1.status_code == 200
        assert mock_intake.return_value.process_inbound_lead.call_count == 1

        # Second call — skipped
        resp2 = client.post(INBOUND_URL, data=INBOUND_FORM)
        assert resp2.status_code == 200
        assert mock_intake.return_value.process_inbound_lead.call_count == 1


# ---------------------------------------------------------------------------
# 3. send_email failure logs external_service_failure audit event
# ---------------------------------------------------------------------------

def test_send_email_failure_audits_external_service_failure(client):
    with (
        patch('src.api.routes.email_webhook.IntakeService') as mock_intake,
        patch('src.api.routes.email_webhook.SendGridClient') as mock_sg,
        patch('src.api.routes.email_webhook.AuditRepository') as mock_audit,
    ):
        mock_intake.return_value.process_inbound_lead.return_value = _mock_intake_result()
        mock_sg.return_value.send_email.return_value = False  # simulate failure
        mock_sg.return_value._from_email = 'noreply@careagency.com'

        resp = client.post(INBOUND_URL, data=INBOUND_FORM)

        assert resp.status_code == 200
        mock_audit.return_value.create_event.assert_called_once()
        call_kwargs = mock_audit.return_value.create_event.call_args.kwargs
        assert call_kwargs['event_type'] == 'external_service_failure'
        assert call_kwargs['event_payload']['vendor'] == 'sendgrid'


# ---------------------------------------------------------------------------
# 4. Sender name is parsed and used in reply greeting
# ---------------------------------------------------------------------------

def test_sender_name_is_extracted_and_passed_to_intake(client):
    with (
        patch('src.api.routes.email_webhook.IntakeService') as mock_intake,
        patch('src.api.routes.email_webhook.SendGridClient') as mock_sg,
    ):
        mock_intake.return_value.process_inbound_lead.return_value = _mock_intake_result()
        mock_sg.return_value.send_email.return_value = True
        mock_sg.return_value._from_email = 'noreply@careagency.com'

        resp = client.post(INBOUND_URL, data=INBOUND_FORM)
        assert resp.status_code == 200

        # The intake request should have the sender's name
        call_args = mock_intake.return_value.process_inbound_lead.call_args
        intake_request = call_args.args[0]
        assert intake_request.name == 'Jane Doe'
        assert intake_request.email == 'jane@example.com'
        assert intake_request.source_channel == 'email'
