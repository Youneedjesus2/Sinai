from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class SendGridClient:
    def __init__(self) -> None:
        import sendgrid as sg_module

        settings = get_settings()
        self._client = sg_module.SendGridAPIClient(api_key=settings.sendgrid_api_key)
        self._from_email = settings.sendgrid_from_email

    def send_email(self, to: str, from_: str, subject: str, body: str) -> bool:
        from sendgrid.helpers.mail import Mail

        try:
            message = Mail(
                from_email=from_,
                to_emails=to,
                subject=subject,
                plain_text_content=body,
            )
            response = self._client.send(message)
            status = response.status_code
            logger.info('sendgrid_email_sent', extra={'vendor': 'sendgrid', 'status_code': status})
            return 200 <= status < 300
        except Exception as exc:
            logger.error('sendgrid_email_failed', extra={'vendor': 'sendgrid', 'error': str(exc)})
            return False
