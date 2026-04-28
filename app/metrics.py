from peewee import fn
from datetime import datetime, timedelta, timezone
from app.models import LLMCall, db


def _ts_isoformat(ts) -> str:
    """Normalize timestamp to ISO string — handles both datetime objects and strings."""
    if isinstance(ts, str):
        return ts
    return ts.isoformat()


def _ts_strftime(ts, fmt: str) -> str:
    """Format timestamp — handles both datetime objects and ISO strings from SQLite."""
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return ts.strftime(fmt)

def get_summary(days: int = 7) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    qs = LLMCall.select().where(LLMCall.timestamp >= since)

    total = qs.count()
    errors = qs.where(LLMCall.status == "error").count()
    total_cost = sum(r.cost_usd for r in qs)
    avg_latency = qs.select(fn.AVG(LLMCall.latency_ms)).scalar() or 0
    total_tokens = sum(r.input_tokens + r.output_tokens for r in qs)

    return {
        "total_calls": total,
        "error_count": errors,
        "error_rate": round((errors / total * 100) if total else 0, 1),
        "total_cost_usd": round(total_cost, 4),
        "avg_latency_ms": round(avg_latency, 1),
        "total_tokens": total_tokens,
    }

def get_calls_over_time(days: int = 7) -> list:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    qs = LLMCall.select().where(LLMCall.timestamp >= since).order_by(LLMCall.timestamp)
    
    # Group by day
    buckets = {}
    for row in qs:
        day = _ts_strftime(row.timestamp, "%Y-%m-%d")
        if day not in buckets:
            buckets[day] = {"calls": 0, "cost": 0.0, "errors": 0}
        buckets[day]["calls"] += 1
        buckets[day]["cost"] = round(buckets[day]["cost"] + row.cost_usd, 6)
        if row.status == "error":
            buckets[day]["errors"] += 1

    return [{"date": k, **v} for k, v in sorted(buckets.items())]

def get_recent_calls(limit: int = 50) -> list:
    qs = LLMCall.select().order_by(LLMCall.timestamp.desc()).limit(limit)
    return [
        {
            "id": r.id,
            "timestamp": _ts_isoformat(r.timestamp),
            "model": r.model,
            "source": r.source,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "latency_ms": r.latency_ms,
            "cost_usd": r.cost_usd,
            "status": r.status,
            "prompt_preview": r.prompt[:120] + "..." if len(r.prompt) > 120 else r.prompt,
            "response_preview": r.response[:120] + "..." if len(r.response) > 120 else r.response,
        }
        for r in qs
    ]

def get_call_detail(call_id: int) -> dict | None:
    try:
        r = LLMCall.get_by_id(call_id)
        return {
            "id": r.id,
            "timestamp": _ts_isoformat(r.timestamp),
            "model": r.model,
            "source": r.source,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "latency_ms": r.latency_ms,
            "cost_usd": r.cost_usd,
            "status": r.status,
            "prompt": r.prompt,
            "response": r.response,
            "error_message": r.error_message,
        }
    except LLMCall.DoesNotExist:
        return None
