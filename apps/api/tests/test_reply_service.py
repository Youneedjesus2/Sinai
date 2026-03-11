from src.schemas.llm import OrchestratorResult
from src.services.reply_service import SMS_MAX_CHARS, ReplyService


def _make_result(reply: str) -> OrchestratorResult:
    return OrchestratorResult(
        detected_intent='general_inquiry',
        follow_up_needed=True,
        escalation_needed=False,
        suggested_next_reply=reply,
    )


def test_sms_reply_short_message_returned_unchanged():
    short = 'Thanks for reaching out. How can we help?'
    result = ReplyService().render_reply(_make_result(short), 'sms')
    assert result == short
    assert len(result) <= SMS_MAX_CHARS


def test_sms_reply_long_message_is_truncated_to_160_chars():
    long_reply = (
        'We offer a wide range of home care services including personal care, '
        'companion care, skilled nursing, respite care, and homemaker services. '
        'Our team of licensed professionals is available seven days a week and '
        'can begin services within 48 hours of your initial assessment.'
    )
    assert len(long_reply) > SMS_MAX_CHARS

    result = ReplyService().render_reply(_make_result(long_reply), 'sms')
    assert len(result) <= SMS_MAX_CHARS


def test_sms_reply_truncates_at_sentence_boundary():
    # Build a reply where the first sentence ends well before 160 chars
    reply = 'We can help. ' + 'A' * 200
    result = ReplyService().render_reply(_make_result(reply), 'sms')
    assert len(result) <= SMS_MAX_CHARS
    # Should end at the period after "We can help"
    assert result.endswith('We can help.')


def test_unknown_channel_falls_back_to_sms_format():
    reply = 'Thanks for reaching out. A coordinator will follow up shortly.'
    sms_result = ReplyService().render_reply(_make_result(reply), 'sms')
    web_result = ReplyService().render_reply(_make_result(reply), 'web')
    chat_result = ReplyService().render_reply(_make_result(reply), 'chat')

    assert sms_result == web_result
    assert sms_result == chat_result
    assert len(web_result) <= SMS_MAX_CHARS


def test_email_reply_includes_greeting_and_closing():
    reply = 'We would be happy to schedule a consultation with you.'
    result = ReplyService().render_reply(_make_result(reply), 'email')

    assert result.startswith('Hello,')
    assert 'Best regards,' in result
    assert reply in result


def test_email_reply_is_not_truncated():
    long_reply = (
        'We offer personal care, companion care, skilled nursing, and respite services. '
        'Our team is available seven days a week. A care coordinator will reach out within '
        'one business day to discuss your needs and schedule a free in-home assessment.'
    )
    result = ReplyService().render_reply(_make_result(long_reply), 'email')
    assert long_reply in result
    assert len(result) > SMS_MAX_CHARS


def test_load_prompt_raises_for_missing_file():
    from src.core.prompts import load_prompt
    import pytest
    with pytest.raises(FileNotFoundError, match='nonexistent/prompt.md'):
        load_prompt('nonexistent/prompt.md')


def test_load_prompt_returns_content_for_existing_file():
    from src.core.prompts import load_prompt
    content = load_prompt('channels/sms_reply.md')
    assert 'SMS' in content
    assert len(content) > 0
