"""Application-level setup functions called once at FastAPI startup."""

from src.core.logging import get_logger

logger = get_logger(__name__)


def setup_phoenix_tracing() -> None:
    """Initialize OpenTelemetry tracing via Arize Phoenix.

    - Registers a TracerProvider pointed at PHOENIX_COLLECTOR_ENDPOINT.
    - Instruments the OpenAI SDK so all LLM calls are captured as spans.
    - Silently skips if PHOENIX_COLLECTOR_ENDPOINT is not set.
    - Logs a warning if the required packages are not installed.
    """
    from src.core.config import get_settings

    settings = get_settings()

    if not settings.phoenix_collector_endpoint:
        logger.info(
            'Phoenix tracing disabled — set PHOENIX_COLLECTOR_ENDPOINT to enable'
        )
        return

    try:
        from phoenix.otel import register

        tracer_provider = register(
            project_name='healthcare-ai-lead-agent',
            endpoint=settings.phoenix_collector_endpoint,
        )
        logger.info(
            'Phoenix tracer registered',
            extra={'endpoint': settings.phoenix_collector_endpoint},
        )
    except ImportError:
        logger.warning(
            'arize-phoenix-otel is not installed — Phoenix tracing disabled'
        )
        return
    except Exception as exc:
        logger.error(
            'Phoenix tracer registration failed',
            extra={'error': str(exc)},
        )
        return

    try:
        from openinference.instrumentation.openai import OpenAIInstrumentor

        OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
        logger.info('OpenAI instrumentation registered with Phoenix tracer')
    except ImportError:
        logger.warning(
            'openinference-instrumentation-openai is not installed — '
            'OpenAI calls will not be traced'
        )
    except Exception as exc:
        logger.error(
            'OpenAI instrumentation setup failed',
            extra={'error': str(exc)},
        )
