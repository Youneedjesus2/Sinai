from pydantic import BaseModel
from openai import OpenAI

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class OrchestratorError(Exception):
    pass


class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=get_settings().openai_api_key)

    def complete_structured(
        self,
        system_prompt: str,
        user_message: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        try:
            response = self.client.beta.chat.completions.parse(
                model='gpt-4o',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message},
                ],
                response_format=response_model,
                max_tokens=1000,
                temperature=0,
            )
            result = response.choices[0].message.parsed
            logger.info('openai_call_success', extra={'vendor': 'openai', 'response_model': response_model.__name__})
            return result
        except Exception as exc:
            logger.error('openai_call_failed', extra={'vendor': 'openai', 'error': str(exc)})
            raise OrchestratorError(str(exc)) from exc
