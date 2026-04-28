import time
from datetime import datetime, timezone
import anthropic
from config import ANTHROPIC_API_KEY, COST_PER_1M_INPUT, COST_PER_1M_OUTPUT
from app.models import LLMCall, db

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def compute_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000 * COST_PER_1M_INPUT) + \
           (output_tokens / 1_000_000 * COST_PER_1M_OUTPUT)

def observed_call(prompt: str, model: str = "claude-haiku-4-5", source: str = "manual", max_tokens: int = 512) -> dict:
    """
    Wraps an Anthropic API call, logs metadata to DB, returns result.
    """
    start = time.time()
    status = "success"
    response_text = ""
    input_tokens = 0
    output_tokens = 0
    error_message = None

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
    except Exception as e:
        status = "error"
        error_message = str(e)

    latency_ms = (time.time() - start) * 1000
    cost_usd = compute_cost(input_tokens, output_tokens)

    LLMCall.create(
        timestamp=datetime.now(timezone.utc),
        model=model,
        prompt=prompt,
        response=response_text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=round(latency_ms, 2),
        cost_usd=round(cost_usd, 6),
        status=status,
        source=source,
        error_message=error_message
    )

    return {
        "response": response_text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": round(latency_ms, 2),
        "cost_usd": round(cost_usd, 6),
        "status": status,
        "error": error_message
    }
