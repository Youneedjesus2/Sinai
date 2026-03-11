import logging

from apscheduler.schedulers.background import BackgroundScheduler

from src.core.config import get_settings

logger = logging.getLogger(__name__)

# Holds the active subscription ID across the process lifetime.
_active_subscription_id: str | None = None

# Module-level scheduler instance so shutdown() can reach it.
_scheduler = BackgroundScheduler()


def register_ringcentral_webhook() -> None:
    """Register an inbound SMS webhook subscription with RingCentral.

    Called on FastAPI startup. Skips silently if RingCentral credentials are
    not configured (empty RINGCENTRAL_CLIENT_ID).
    """
    global _active_subscription_id

    settings = get_settings()

    if not settings.ringcentral_client_id:
        logger.info('RingCentral not configured — skipping webhook registration')
        return

    if not settings.ringcentral_webhook_url:
        logger.warning(
            'RINGCENTRAL_WEBHOOK_URL is not set — cannot register webhook subscription'
        )
        return

    # Re-use an existing subscription ID if provided via environment.
    existing_id = settings.ringcentral_subscription_id
    if existing_id:
        logger.info(
            'RingCentral subscription already configured — ID: %s', existing_id
        )
        _active_subscription_id = existing_id
        return

    try:
        from src.integrations.ringcentral_client import RingCentralClient

        subscription_id = RingCentralClient().register_webhook_subscription(
            settings.ringcentral_webhook_url
        )
        _active_subscription_id = subscription_id
        logger.info(
            'RingCentral webhook registered — ID: %s  '
            'Set RINGCENTRAL_SUBSCRIPTION_ID=%s in your environment to persist across restarts.',
            subscription_id,
            subscription_id,
        )
    except Exception:
        logger.exception('RingCentral webhook registration failed')


def schedule_subscription_renewal() -> None:
    """Start a background scheduler that renews the RingCentral subscription
    every 6 days (before the 7-day TTL expires).

    Logs clearly on each run so expiry problems are visible in monitoring.
    """
    settings = get_settings()
    if not settings.ringcentral_client_id:
        return

    def _renew() -> None:
        sid = _active_subscription_id
        logger.info('RingCentral subscription renewal task running — ID: %s', sid)
        if not sid:
            logger.warning(
                'RingCentral subscription renewal: no active subscription ID. '
                'Inbound SMS may stop working if the subscription has expired.'
            )
            return

        try:
            from src.integrations.ringcentral_client import RingCentralClient

            success = RingCentralClient().renew_subscription(sid)
            if success:
                logger.info('RingCentral subscription renewed successfully — ID: %s', sid)
            else:
                logger.error(
                    'RingCentral subscription renewal FAILED — ID: %s. '
                    'Inbound SMS will stop working when the subscription expires.',
                    sid,
                )
        except Exception:
            logger.exception(
                'RingCentral subscription renewal raised an exception — ID: %s', sid
            )

    _scheduler.add_job(_renew, 'interval', days=6, id='rc_subscription_renewal')
    _scheduler.start()
    logger.info('RingCentral subscription renewal task scheduled (every 6 days)')


def shutdown_scheduler() -> None:
    """Gracefully stop the background scheduler on FastAPI shutdown."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info('RingCentral renewal scheduler stopped')
