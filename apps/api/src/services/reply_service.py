from src.core.prompts import load_prompt
from src.schemas.llm import OrchestratorResult

SMS_MAX_CHARS = 160
SUPPORTED_CHANNELS = ('sms', 'email')


class ReplyService:
    def render_reply(self, orchestration: OrchestratorResult, channel: str) -> str:
        effective_channel = channel if channel in SUPPORTED_CHANNELS else 'sms'

        try:
            load_prompt(f'channels/{effective_channel}_reply.md')
        except FileNotFoundError:
            effective_channel = 'sms'

        reply = orchestration.suggested_next_reply

        if effective_channel == 'sms':
            return self._format_sms(reply)
        elif effective_channel == 'email':
            return self._format_email(reply)

        return self._format_sms(reply)

    def _format_sms(self, text: str) -> str:
        text = text.strip()
        if len(text) <= SMS_MAX_CHARS:
            return text

        truncated = text[:SMS_MAX_CHARS - 3]
        boundary = max(truncated.rfind('.'), truncated.rfind('?'), truncated.rfind('!'))
        if boundary >= 0:
            return text[:boundary + 1]

        return truncated + '...'

    def _format_email(self, text: str) -> str:
        text = text.strip()
        return f'Hello,\n\n{text}\n\nBest regards,\nThe Care Team'
