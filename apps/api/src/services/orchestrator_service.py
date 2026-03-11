from pathlib import Path

from src.core.logging import get_logger
from src.integrations.openai_client import OpenAIClient, OrchestratorError
from src.schemas.llm import OrchestratorResult, RetrievalResult

logger = get_logger(__name__)

PROMPT_PATH = Path(__file__).parents[4] / 'prompts' / 'tasks' / 'classify_intent.md'

SAFE_FALLBACK_REPLY = 'Thanks for reaching out. Our team will follow up shortly.'
NO_CONTEXT_REPLY = (
    "I don't have enough reliable information to answer that right now, "
    'but I can connect you with a team member.'
)


class OrchestratorService:
    @staticmethod
    def process_inbound_message(
        message_body: str,
        retrieval_result: RetrievalResult | None = None,
    ) -> OrchestratorResult:
        # Safe failure rule: if retrieval ran but found no trusted context,
        # escalate immediately — do NOT pass empty context to the LLM.
        if retrieval_result is not None and not retrieval_result.context_found:
            logger.info(
                'orchestrator_escalating_no_context',
                extra={'detected_intent': 'escalation', 'escalation_needed': True},
            )
            return OrchestratorResult(
                detected_intent='escalation',
                follow_up_needed=True,
                escalation_needed=True,
                suggested_next_reply=NO_CONTEXT_REPLY,
            )

        try:
            system_prompt = PROMPT_PATH.read_text()

            if retrieval_result is not None and retrieval_result.context_found:
                context_block = '\n\n'.join(retrieval_result.context_chunks)
                system_prompt = (
                    system_prompt
                    + '\n\n## APPROVED CONTEXT\n'
                    + 'Use the following approved information to answer the lead\'s question:\n\n'
                    + context_block
                )

            result = OpenAIClient().complete_structured(
                system_prompt=system_prompt,
                user_message=message_body,
                response_model=OrchestratorResult,
            )
            logger.info(
                'orchestration_completed',
                extra={'detected_intent': result.detected_intent, 'escalation_needed': result.escalation_needed},
            )
            return result
        except (OrchestratorError, Exception) as exc:
            logger.error('orchestrator_fallback_triggered', extra={'error': str(exc)})
            return OrchestratorResult(
                detected_intent='fallback',
                follow_up_needed=True,
                escalation_needed=False,
                suggested_next_reply=SAFE_FALLBACK_REPLY,
            )
