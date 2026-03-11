"""Tests for src/core/logging.py structured JSON logging."""

import json
import logging
from io import StringIO
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# 1. get_logger returns a stdlib Logger instance
# ---------------------------------------------------------------------------

def test_get_logger_returns_logger():
    from src.core.logging import get_logger

    log = get_logger('test.module')
    assert isinstance(log, logging.Logger)
    assert log.name == 'test.module'


# ---------------------------------------------------------------------------
# 2. Two calls with the same name return the same logger
# ---------------------------------------------------------------------------

def test_get_logger_same_name_returns_same_instance():
    from src.core.logging import get_logger

    a = get_logger('same.name')
    b = get_logger('same.name')
    assert a is b


# ---------------------------------------------------------------------------
# 3. JSON formatter produces valid JSON with required keys
# ---------------------------------------------------------------------------

def test_json_formatter_produces_valid_json():
    from src.core.logging import _JsonFormatter

    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='',
        lineno=0,
        msg='test event',
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed['level'] == 'INFO'
    assert parsed['name'] == 'test'
    assert parsed['message'] == 'test event'
    assert 'timestamp' in parsed


# ---------------------------------------------------------------------------
# 4. Extra fields appear in the "extra" block of JSON output
# ---------------------------------------------------------------------------

def test_json_formatter_includes_extra_fields():
    from src.core.logging import _JsonFormatter

    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='',
        lineno=0,
        msg='lead event',
        args=(),
        exc_info=None,
    )
    record.lead_id = 42
    record.agency_id = 'acme'

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed['extra']['lead_id'] == 42
    assert parsed['extra']['agency_id'] == 'acme'


# ---------------------------------------------------------------------------
# 5. Exception info is captured in extra.traceback
# ---------------------------------------------------------------------------

def test_json_formatter_captures_exception():
    from src.core.logging import _JsonFormatter

    formatter = _JsonFormatter()
    try:
        raise ValueError('test error')
    except ValueError:
        import sys
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name='test',
        level=logging.ERROR,
        pathname='',
        lineno=0,
        msg='something failed',
        args=(),
        exc_info=exc_info,
    )
    output = formatter.format(record)
    parsed = json.loads(output)

    assert 'traceback' in parsed['extra']
    assert 'ValueError' in parsed['extra']['traceback']


# ---------------------------------------------------------------------------
# 6. Logging from IntakeService doesn't raise
# ---------------------------------------------------------------------------

def test_intake_service_logging_does_not_raise(reset_db):
    """Verify that structured log calls in IntakeService don't throw errors."""
    from src.core.db import SessionLocal
    from src.services.intake_service import IntakeService
    from src.schemas.lead import InboundLeadRequest
    from src.schemas.llm import OrchestratorResult, RetrievalResult
    from unittest.mock import patch

    db = SessionLocal()
    try:
        with (
            patch('src.services.intake_service.RetrievalService') as mock_ret,
            patch('src.services.intake_service.OrchestratorService') as mock_orch,
            patch('src.services.intake_service.ReplyService') as mock_reply,
        ):
            mock_ret.return_value.retrieve.return_value = RetrievalResult(
                context_chunks=[],
                confidence_score=0.0,
                sources=[],
                context_found=False,
            )
            mock_orch.process_inbound_message.return_value = OrchestratorResult(
                detected_intent='general_inquiry',
                follow_up_needed=False,
                escalation_needed=False,
                suggested_next_reply='Thanks!',
            )
            mock_reply.return_value.render_reply.return_value = 'Thanks!'

            # Should not raise
            payload = InboundLeadRequest(
                agency_id='test-agency',
                source_channel='sms',
                message_body='I need help.',
            )
            IntakeService(db).process_inbound_lead(payload)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 7. Logging from OrchestratorService doesn't raise
# ---------------------------------------------------------------------------

def test_orchestrator_service_logging_does_not_raise():
    from src.services.orchestrator_service import OrchestratorService
    from src.schemas.llm import OrchestratorResult, RetrievalResult
    from unittest.mock import patch

    no_context = RetrievalResult(
        context_chunks=[],
        confidence_score=0.0,
        sources=[],
        context_found=False,
    )
    # This path calls logger.info internally — should not raise
    result = OrchestratorService.process_inbound_message('hi', no_context)
    assert result.escalation_needed is True


# ---------------------------------------------------------------------------
# 8. setup_phoenix_tracing skips gracefully when endpoint is not set
# ---------------------------------------------------------------------------

def test_setup_phoenix_tracing_skips_when_not_configured():
    """setup_phoenix_tracing must not raise when PHOENIX_COLLECTOR_ENDPOINT is absent."""
    from src.core.app import setup_phoenix_tracing

    # Should complete without error — endpoint is None in test env
    setup_phoenix_tracing()
