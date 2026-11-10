"""LLM provider configuration.

Every provider below exposes an OpenAI-compatible Chat Completions API,
so one client library works for all of them. Switch providers by changing
LLM_PROVIDER in your .env file — no code changes needed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str | None
    key_env: str
    default_model: str


PROVIDERS: dict[str, Provider] = {
    # Free tier: https://aistudio.google.com/apikey
    "gemini": Provider(
        "gemini",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        "GEMINI_API_KEY",
        "gemini-2.5-flash",
    ),
    # Free tier: https://console.groq.com/keys
    "groq": Provider(
        "groq",
        "https://api.groq.com/openai/v1",
        "GROQ_API_KEY",
        "llama-3.3-70b-versatile",
    ),
    "openai": Provider("openai", None, "OPENAI_API_KEY", "gpt-4o-mini"),
    "anthropic": Provider(
        "anthropic",
        "https://api.anthropic.com/v1/",
        "ANTHROPIC_API_KEY",
        "claude-haiku-4-5",
    ),
}


def make_client() -> tuple[OpenAI, str]:
    """Build a client for the provider named in LLM_PROVIDER (default: gemini)."""
    name = os.getenv("LLM_PROVIDER", "gemini").lower()
    if name not in PROVIDERS:
        raise SystemExit(f"Unknown LLM_PROVIDER '{name}'. Choose one of: {', '.join(PROVIDERS)}")

    provider = PROVIDERS[name]
    api_key = os.getenv(provider.key_env)
    if not api_key:
        raise SystemExit(f"Missing {provider.key_env}. Copy .env.example to .env and add your key.")

    client = OpenAI(api_key=api_key, base_url=provider.base_url)
    model = os.getenv("LLM_MODEL", provider.default_model)
    return client, model
