"""The agent loop.

1. Send the conversation + tool schemas to the model.
2. If the model asks for tool calls, run them and append the results.
3. Repeat until the model replies with plain text (or we hit max_steps).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .tools import TOOL_SCHEMAS, run_tool

SYSTEM_PROMPT = (
    "You are a concise, helpful assistant running in a terminal. "
    "Use the provided tools for arithmetic, the current time, and weather. "
    "Never guess numbers you could calculate. Keep answers short."
)


@dataclass
class Agent:
    client: Any  # an openai.OpenAI-compatible client
    model: str
    max_steps: int = 6
    on_tool_call: Callable[[str, str, str], None] | None = None
    messages: list[dict[str, Any]] = field(default_factory=lambda: [{"role": "system", "content": SYSTEM_PROMPT}])

    def ask(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        for _ in range(self.max_steps):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=TOOL_SCHEMAS,
            )
            msg = response.choices[0].message
            tool_calls = msg.tool_calls or []

            # Record the assistant turn (including any tool requests) in history.
            entry: dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
            if tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in tool_calls
                ]
            self.messages.append(entry)

            if not tool_calls:
                return msg.content or ""

            for tc in tool_calls:
                result = run_tool(tc.function.name, tc.function.arguments)
                if self.on_tool_call:
                    self.on_tool_call(tc.function.name, tc.function.arguments, result)
                self.messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        return "I stopped after too many tool steps. Try a simpler question."
