from pathlib import Path

from src.integrations.openai_client import OpenAIClient, OrchestratorError
from src.schemas.llm import OrchestratorResult

PROMPT_PATH = Path(__file__).parents[4] / 'prompts' / 'tasks' / 'classify_intent.md'

FALLBACK_RESULT = OrchestratorResult(
    detected_intent='fallback',
    follow_up_needed=True,
    escalation_needed=False,
    suggested_next_reply='Thanks for reaching out. Our team will follow up shortly.',
)


class OrchestratorService:
    @staticmethod
    def process_inbound_message(message_body: str) -> OrchestratorResult:
        try:
            system_prompt = PROMPT_PATH.read_text()
            return OpenAIClient().complete_structured(
                system_prompt=system_prompt,
                user_message=message_body,
                response_model=OrchestratorResult,
            )
        except (OrchestratorError, Exception):
            return OrchestratorResult(
                detected_intent='fallback',
                follow_up_needed=True,
                escalation_needed=False,
                suggested_next_reply='Thanks for reaching out. Our team will follow up shortly.',
            )
