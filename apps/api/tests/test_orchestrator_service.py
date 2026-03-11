from unittest.mock import MagicMock, patch

from src.schemas.llm import OrchestratorResult
from src.services.orchestrator_service import OrchestratorService


def _make_openai_mock(result: OrchestratorResult) -> MagicMock:
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.parsed = result
    mock_client.beta.chat.completions.parse.return_value = mock_response
    return mock_client


def test_orchestrator_detects_appointment_request():
    appointment_result = OrchestratorResult(
        detected_intent='appointment_request',
        follow_up_needed=True,
        escalation_needed=False,
        suggested_next_reply='I can help schedule that. What day and time works best for you?',
    )

    with patch('src.integrations.openai_client.OpenAI', return_value=_make_openai_mock(appointment_result)):
        result = OrchestratorService.process_inbound_message('I want to book an appointment this Friday')

    assert result.detected_intent == 'appointment_request'
    assert result.follow_up_needed is True
    assert result.escalation_needed is False
    assert 'schedule' in result.suggested_next_reply.lower() or 'help' in result.suggested_next_reply.lower()


def test_orchestrator_returns_fallback_when_openai_raises():
    with patch('src.integrations.openai_client.OpenAI') as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.beta.chat.completions.parse.side_effect = Exception('API error')

        result = OrchestratorService.process_inbound_message('I need help right away')

    assert result.detected_intent == 'fallback'
    assert result.follow_up_needed is True
    assert result.escalation_needed is False
    assert 'follow up' in result.suggested_next_reply.lower()
