"""
Tests for app/logger.py — observed_call() wrapper.
Patches the Anthropic client so no real API calls are made.
Uses an in-memory SQLite database.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from peewee import SqliteDatabase
from app.models import LLMCall

# ---------------------------------------------------------------------------
# Test DB setup
# ---------------------------------------------------------------------------

TEST_DB = SqliteDatabase(":memory:")


@pytest.fixture(autouse=True)
def setup_db():
    TEST_DB.bind([LLMCall], bind_refs=False, bind_backrefs=False)
    TEST_DB.connect()
    TEST_DB.create_tables([LLMCall])
    yield
    TEST_DB.drop_tables([LLMCall])
    TEST_DB.close()


# ---------------------------------------------------------------------------
# Helpers — fake Anthropic response
# ---------------------------------------------------------------------------

def _fake_response(text="hello", input_tokens=10, output_tokens=5):
    content = MagicMock()
    content.text = text
    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens
    resp = MagicMock()
    resp.content = [content]
    resp.usage = usage
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@patch("app.logger.client")
def test_observed_call_success_logs_to_db(mock_client):
    from app.logger import observed_call

    mock_client.messages.create.return_value = _fake_response(
        text="Paris", input_tokens=20, output_tokens=3
    )

    result = observed_call(prompt="What is the capital of France?", source="test")

    # Return value shape
    assert result["status"] == "success"
    assert result["response"] == "Paris"
    assert result["input_tokens"] == 20
    assert result["output_tokens"] == 3
    assert result["latency_ms"] >= 0
    assert result["error"] is None

    # DB record created
    assert LLMCall.select().count() == 1
    row = LLMCall.get()
    assert row.prompt == "What is the capital of France?"
    assert row.response == "Paris"
    assert row.status == "success"
    assert row.source == "test"
    assert row.input_tokens == 20
    assert row.output_tokens == 3


@patch("app.logger.client")
def test_observed_call_error_logs_to_db(mock_client):
    from app.logger import observed_call

    mock_client.messages.create.side_effect = Exception("API timeout")

    result = observed_call(prompt="trigger error", source="test")

    assert result["status"] == "error"
    assert "API timeout" in result["error"]
    assert result["response"] == ""
    assert result["input_tokens"] == 0

    row = LLMCall.get()
    assert row.status == "error"
    assert "API timeout" in row.error_message


@patch("app.logger.client")
def test_observed_call_cost_calculation(mock_client):
    from app.logger import observed_call
    from config import COST_PER_1M_INPUT, COST_PER_1M_OUTPUT

    mock_client.messages.create.return_value = _fake_response(
        input_tokens=1_000_000, output_tokens=1_000_000
    )

    result = observed_call(prompt="cost test")
    expected = round(COST_PER_1M_INPUT + COST_PER_1M_OUTPUT, 6)
    assert result["cost_usd"] == pytest.approx(expected, rel=1e-3)


@patch("app.logger.client")
def test_observed_call_default_model(mock_client):
    from app.logger import observed_call

    mock_client.messages.create.return_value = _fake_response()
    observed_call(prompt="default model test")

    call_kwargs = mock_client.messages.create.call_args
    assert call_kwargs.kwargs["model"] == "claude-haiku-4-5"


@patch("app.logger.client")
def test_observed_call_custom_model(mock_client):
    from app.logger import observed_call

    mock_client.messages.create.return_value = _fake_response()
    observed_call(prompt="sonnet test", model="claude-sonnet-4-6")

    call_kwargs = mock_client.messages.create.call_args
    assert call_kwargs.kwargs["model"] == "claude-sonnet-4-6"
