# LumenStack · Observe

**LLM Observability Dashboard** — part of the [LumenStack](https://ado-runner.com) suite.

Wraps Anthropic API calls to track runtime behavior in production: latency, token usage, cost, error rates, and full prompt/response logging. Gives AI engineers production-grade visibility into any system built on Claude.

## Features

- **Live dashboard** — calls over time, avg latency, total cost, error rate
- **Prompt/response log** — inspect every LLM call with full metadata
- **Test query panel** — send prompts directly through the observed pipeline
- **SQLite persistence** — lightweight, zero-dependency storage
- **Production-ready** — Gunicorn + Nginx + systemd deployable

## Stack

- Python / Flask
- Peewee ORM / SQLite
- Anthropic API (`anthropic>=0.96.0`)
- Chart.js
- Gunicorn (production)

## Setup

```bash
git clone https://github.com/ohdasdiego/lumenstack-observe
cd lumenstack-observe
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your ANTHROPIC_API_KEY
python app.py
```

## Production (VPS)

```bash
bash run.sh
```

Configure Nginx to proxy `127.0.0.1:5009` → `lumen.observe.ado-runner.com`

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

## Cost Tracking

Token costs are estimated using Anthropic's published per-model pricing (see `config.py`).
Update `COST_PER_1M_INPUT` / `COST_PER_1M_OUTPUT` if you switch models.

| Model | Input / 1M | Output / 1M |
|---|---|---|
| claude-haiku-4-5 | $0.80 | $4.00 |
| claude-haiku-3 | $0.25 | $1.25 |
| claude-sonnet-4-6 | $3.00 | $15.00 |

## LumenStack Suite

LumenStack is a suite of LLM operations tools for AI engineers who need visibility into the full lifecycle of language model systems — from runtime monitoring and prompt engineering to quality evaluation and model comparison.

| # | Tool | URL | Description |
|---|---|---|---|
| **1** | **Observe ← you are here** | lumen.observe.ado-runner.com | Runtime LLM observability |
| 2 | Eval | lumen.eval.ado-runner.com | Output quality evaluation |
| 3 | Prompts | lumen.prompts.ado-runner.com | Prompt version management |
| 4 | Models | lumen.models.ado-runner.com | Model comparison & benchmarking |

Part of the [ADOStack](https://ado-runner.com) family of AI ops tools.
