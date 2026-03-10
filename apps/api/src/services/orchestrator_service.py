from src.schemas.llm import OrchestratorResult


class OrchestratorService:
    @staticmethod
    def process_inbound_message(message_body: str) -> OrchestratorResult:
        lower = message_body.lower()
        raw_result = {
            'detected_intent': 'general_inquiry',
            'follow_up_needed': True,
            'escalation_needed': False,
            'suggested_next_reply': 'Thanks for reaching out. Could you share your preferred appointment time?',
        }

        if any(token in lower for token in ['urgent', 'pain', 'emergency']):
            raw_result = {
                'detected_intent': 'urgent_support',
                'follow_up_needed': True,
                'escalation_needed': True,
                'suggested_next_reply': 'Thank you for your message. A care coordinator will contact you immediately.',
            }
        elif 'appointment' in lower or 'book' in lower:
            raw_result = {
                'detected_intent': 'appointment_request',
                'follow_up_needed': True,
                'escalation_needed': False,
                'suggested_next_reply': 'I can help schedule that. What day and time works best for you?',
            }

        try:
            return OrchestratorResult.model_validate(raw_result)
        except Exception:
            return OrchestratorResult(
                detected_intent='fallback',
                follow_up_needed=True,
                escalation_needed=False,
                suggested_next_reply='Thanks for reaching out. Our team will follow up shortly.',
            )
