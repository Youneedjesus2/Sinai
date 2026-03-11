import logging

from src.core.config import get_settings

logger = logging.getLogger(__name__)

RINGCENTRAL_SERVER = 'https://platform.ringcentral.com'

SMS_EVENT_FILTER = '/restapi/v1.0/account/~/extension/~/message-store/instant?type=SMS'
SUBSCRIPTION_TTL_SECONDS = 604800  # 7 days


class RingCentralClient:
    def __init__(self) -> None:
        from ringcentral import SDK

        settings = get_settings()
        self._sdk = SDK(
            settings.ringcentral_client_id,
            settings.ringcentral_client_secret,
            RINGCENTRAL_SERVER,
        )
        self._platform = self._sdk.platform()
        self._platform.login(jwt=settings.ringcentral_jwt_token)
        self._from_number = settings.ringcentral_from_number
        self._verification_token = settings.ringcentral_webhook_verification_token

    def send_sms(self, to: str, body: str) -> str | None:
        try:
            response = self._platform.post(
                '/restapi/v1.0/account/~/extension/~/sms',
                {
                    'from': {'phoneNumber': self._from_number},
                    'to': [{'phoneNumber': to}],
                    'text': body,
                },
            )
            data = response.json()
            msg_id = data.get('id')
            logger.info('RingCentral SMS sent to %s — message ID: %s', to, msg_id)
            return str(msg_id) if msg_id else None
        except Exception as exc:
            logger.error('RingCentral send_sms failed: %s', exc)
            return None

    def register_webhook_subscription(self, webhook_url: str) -> str:
        response = self._platform.post(
            '/restapi/v1.0/subscription',
            {
                'eventFilters': [SMS_EVENT_FILTER],
                'deliveryMode': {
                    'transportType': 'WebHook',
                    'address': webhook_url,
                    'verificationToken': self._verification_token,
                    'expiresIn': SUBSCRIPTION_TTL_SECONDS,
                },
            },
        )
        data = response.json()
        subscription_id = str(data['id'])
        logger.info(
            'RingCentral webhook subscription registered — ID: %s  expires in %s s',
            subscription_id,
            SUBSCRIPTION_TTL_SECONDS,
        )
        return subscription_id

    def renew_subscription(self, subscription_id: str) -> bool:
        try:
            self._platform.post(
                f'/restapi/v1.0/subscription/{subscription_id}/renew'
            )
            logger.info('RingCentral subscription renewed — ID: %s', subscription_id)
            return True
        except Exception as exc:
            logger.error(
                'RingCentral subscription renewal FAILED — ID: %s  error: %s',
                subscription_id,
                exc,
            )
            return False
