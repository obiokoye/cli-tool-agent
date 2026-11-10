"""Tests run without any API key: a fake client replays scripted model replies."""

from __future__ import annotations

import json
from types import SimpleNamespace as NS

from agent import Agent
from agent.tools import calculator, current_time, run_tool


# --- tools -----------------------------------------------------------------

def test_calculator_basic():
    assert calculator("(12.5 * 4) / 2")["result"] == 25


def test_calculator_rejects_code():
    assert "error" in calculator("__import__('os').system('ls')")


def test_calculator_division_by_zero():
    assert "error" in calculator("1/0")


def test_current_time_unknown_zone():
    assert "error" in current_time("Mars/Olympus")


def test_run_tool_unknown():
    assert "unknown tool" in run_tool("nope", "{}")


# --- agent loop ------------------------------------------------------------

def _tool_call(call_id, name, args):
    return NS(id=call_id, function=NS(name=name, arguments=json.dumps(args)))


def _reply(content=None, tool_calls=None):
    return NS(choices=[NS(message=NS(content=content, tool_calls=tool_calls))])


class FakeClient:
    def __init__(self, replies):
        self._replies = iter(replies)
        self.calls = []
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kwargs):
        # Snapshot messages: the agent keeps appending to the same list.
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        return next(self._replies)


def test_agent_runs_tool_then_answers():
    client = FakeClient([
        _reply(tool_calls=[_tool_call("c1", "calculator", {"expression": "84000 * 0.15"})]),
        _reply(content="15% of 84,000 is 12,600."),
    ])
    seen = []
    agent = Agent(client=client, model="fake", on_tool_call=lambda n, a, r: seen.append((n, json.loads(r))))

    answer = agent.ask("What's 15% of 84000?")

    assert answer == "15% of 84,000 is 12,600."
    assert seen[0][0] == "calculator" and seen[0][1]["result"] == 12600
    # The tool result must be sent back to the model on the second call.
    second_call_msgs = client.calls[1]["messages"]
    assert second_call_msgs[-1]["role"] == "tool"
    assert second_call_msgs[-1]["tool_call_id"] == "c1"


def test_agent_stops_after_max_steps():
    looping = [_reply(tool_calls=[_tool_call(f"c{i}", "current_time", {})]) for i in range(10)]
    agent = Agent(client=FakeClient(looping), model="fake", max_steps=3)
    assert "too many tool steps" in agent.ask("loop forever")
