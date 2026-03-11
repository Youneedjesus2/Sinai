from pydantic import BaseModel
from openai import OpenAI

from src.core.config import get_settings


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
                model='gpt-5-mini',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message},
                ],
                response_format=response_model,
                max_tokens=1000,
                temperature=0,
            )
            return response.choices[0].message.parsed
        except Exception as exc:
            raise OrchestratorError(str(exc)) from exc
