from src.services.orchestrator_service import OrchestratorService


def test_orchestrator_detects_appointment_request():
    result = OrchestratorService.process_inbound_message('I want to book an appointment this Friday')

    assert result.detected_intent == 'appointment_request'
    assert result.follow_up_needed is True
    assert result.escalation_needed is False
    assert 'schedule' in result.suggested_next_reply.lower() or 'help' in result.suggested_next_reply.lower()
