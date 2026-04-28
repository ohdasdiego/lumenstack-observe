"""
Tests for app/metrics.py — query helpers over the LLMCall table.
Uses a temporary in-memory SQLite database; no API calls made.
"""

import pytest
from datetime import datetime, timedelta, timezone
from peewee import SqliteDatabase
from app.models import LLMCall

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_DB = SqliteDatabase(":memory:")


@pytest.fixture(autouse=True)
def setup_db():
    """Bind LLMCall to an in-memory DB for each test, then tear down."""
    TEST_DB.bind([LLMCall], bind_refs=False, bind_backrefs=False)
    if TEST_DB.is_closed():
        TEST_DB.connect()
    TEST_DB.create_tables([LLMCall])
    yield
    LLMCall.delete().execute()  # clear rows between tests (avoids lock on drop)
    TEST_DB.close()


def _make_call(**kwargs):
    defaults = dict(
        timestamp=datetime.now(timezone.utc),
        model="claude-haiku-4-5",
        prompt="test prompt",
        response="test response",
        input_tokens=100,
        output_tokens=50,
        latency_ms=320.0,
        cost_usd=0.000280,
        status="success",
        source="test",
        error_message=None,
    )
    defaults.update(kwargs)
    return LLMCall.create(**defaults)


# ---------------------------------------------------------------------------
# get_summary
# ---------------------------------------------------------------------------

def test_get_summary_empty():
    from app.metrics import get_summary
    s = get_summary(days=7)
    assert s["total_calls"] == 0
    assert s["error_count"] == 0
    assert s["error_rate"] == 0.0
    assert s["total_cost_usd"] == 0.0
    assert s["avg_latency_ms"] == 0
    assert s["total_tokens"] == 0


def test_get_summary_counts():
    from app.metrics import get_summary
    _make_call(status="success", input_tokens=100, output_tokens=50, cost_usd=0.0001, latency_ms=200.0)
    _make_call(status="success", input_tokens=200, output_tokens=80, cost_usd=0.0002, latency_ms=400.0)
    _make_call(status="error",   input_tokens=0,   output_tokens=0,  cost_usd=0.0,    latency_ms=50.0)

    s = get_summary(days=7)
    assert s["total_calls"] == 3
    assert s["error_count"] == 1
    assert round(s["error_rate"], 1) == 33.3
    assert s["total_tokens"] == 430
    assert s["avg_latency_ms"] == pytest.approx(216.7, abs=1)


def test_get_summary_excludes_old_calls():
    from app.metrics import get_summary
    old_ts = datetime.now(timezone.utc) - timedelta(days=10)
    _make_call(timestamp=old_ts)
    _make_call()  # recent

    s = get_summary(days=7)
    assert s["total_calls"] == 1


# ---------------------------------------------------------------------------
# get_calls_over_time
# ---------------------------------------------------------------------------

def test_get_calls_over_time_grouped_by_day():
    from app.metrics import get_calls_over_time
    today = datetime.now(timezone.utc)
    yesterday = today - timedelta(days=1)

    _make_call(timestamp=today)
    _make_call(timestamp=today)
    _make_call(timestamp=yesterday, status="error")

    rows = get_calls_over_time(days=7)
    assert len(rows) == 2

    day_map = {r["date"]: r for r in rows}
    today_key = today.strftime("%Y-%m-%d")
    yesterday_key = yesterday.strftime("%Y-%m-%d")

    assert day_map[today_key]["calls"] == 2
    assert day_map[today_key]["errors"] == 0
    assert day_map[yesterday_key]["calls"] == 1
    assert day_map[yesterday_key]["errors"] == 1


# ---------------------------------------------------------------------------
# get_recent_calls
# ---------------------------------------------------------------------------

def test_get_recent_calls_order_and_limit():
    from app.metrics import get_recent_calls
    for i in range(5):
        _make_call(prompt=f"prompt {i}", timestamp=datetime.now(timezone.utc) - timedelta(minutes=5 - i))

    calls = get_recent_calls(limit=3)
    assert len(calls) == 3
    # Most recent first
    assert calls[0]["timestamp"] > calls[1]["timestamp"]


def test_get_recent_calls_prompt_preview_truncated():
    from app.metrics import get_recent_calls
    long_prompt = "x" * 200
    _make_call(prompt=long_prompt)
    calls = get_recent_calls(limit=1)
    assert calls[0]["prompt_preview"].endswith("...")
    assert len(calls[0]["prompt_preview"]) <= 123  # 120 + "..."


# ---------------------------------------------------------------------------
# get_call_detail
# ---------------------------------------------------------------------------

def test_get_call_detail_found():
    from app.metrics import get_call_detail
    row = _make_call(prompt="detail test", response="the answer")
    detail = get_call_detail(row.id)
    assert detail is not None
    assert detail["prompt"] == "detail test"
    assert detail["response"] == "the answer"


def test_get_call_detail_not_found():
    from app.metrics import get_call_detail
    assert get_call_detail(99999) is None
