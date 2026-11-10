# 🔧 CLI Tool Agent

> **Day 1 of [30 Days of AI Agents](https://github.com/obiokoye)**: a terminal AI agent that decides when to call tools (calculator, clock, live weather) and uses the results to answer.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Tests](https://github.com/obiokoye/cli-tool-agent/actions/workflows/tests.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-green)

```text
you › What's 7.5% VAT on ₦250,000, and what time is it in Luxembourg?
  🔧 calculator({"expression": "250000 * 0.075"}) → {"result": 18750.0}
  🔧 current_time({"timezone": "Europe/Luxembourg"}) → {"iso": "2026-11-10T12:40:02+01:00", "weekday": "Tuesday"}
agent › VAT is ₦18,750. It's 12:40 on Tuesday in Luxembourg.
```

## What it shows

- **Tool calling (function calling)**: the model chooses tools and arguments from JSON Schemas. This is the core building block of every AI agent.
- **The agent loop**: call the model, run the requested tools, feed the results back, and repeat until it gives a final answer. A `max_steps` limit stops runaway loops.
- **Safe tools**: the calculator parses an AST instead of calling `eval()`, so the model can't run arbitrary code.
- **Swappable providers**: Gemini, Groq, OpenAI or Anthropic through one OpenAI-compatible client. Switch with a single `.env` value.
- **Tests without API keys**: a fake client replays scripted model replies, so CI runs for free.

## Quick start

```bash
git clone https://github.com/obiokoye/cli-tool-agent.git
cd cli-tool-agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # add a free Gemini key from https://aistudio.google.com/apikey
python main.py
```

One-shot mode: `python main.py "How many days until 1 January 2027?"`

## Switching providers

| `LLM_PROVIDER` | Key variable        | Default model             | Free tier |
|----------------|---------------------|---------------------------|-----------|
| `gemini`       | `GEMINI_API_KEY`    | `gemini-2.5-flash`        | ✅ |
| `groq`         | `GROQ_API_KEY`      | `llama-3.3-70b-versatile` | ✅ |
| `openai`       | `OPENAI_API_KEY`    | `gpt-4o-mini`             | ❌ |
| `anthropic`    | `ANTHROPIC_API_KEY` | `claude-haiku-4-5`        | ❌ |

Override the model with `LLM_MODEL=...`.

## Project structure

```text
agent/
  core.py       # the agent loop
  tools.py      # tool functions + JSON schemas + dispatcher
  providers.py  # provider config (OpenAI-compatible endpoints)
main.py         # terminal UI (rich)
tests/          # pytest, no network or API key needed
```

## Adding a tool

1. Write a function in `agent/tools.py` that returns a `dict`.
2. Add it to `TOOLS` and give it a schema in `TOOL_SCHEMAS`.

The model will start using it automatically when it's relevant.

## Run tests

```bash
pytest -q
```

New to Python? See **[LEARN.md](LEARN.md)**, which walks through this codebase in Laravel terms.

---

MIT © Nicholas Okoye
