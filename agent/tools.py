"""Tools the agent can call.

Each tool is a plain Python function plus a JSON Schema that tells the
model what the tool does and what arguments it takes. The model never
runs code itself — it asks us to run a tool, and we send back the result.
"""

from __future__ import annotations

import ast
import json
import operator
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# ---------------------------------------------------------------------------
# calculator — safe arithmetic (no eval!)
# ---------------------------------------------------------------------------

_OPS: dict[type, Callable[..., float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("exponent too large")
        return _OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("only numbers and + - * / // % ** are allowed")


def calculator(expression: str) -> dict[str, Any]:
    """Evaluate an arithmetic expression like '(12.5 * 4) / 3'."""
    try:
        tree = ast.parse(expression, mode="eval")
        return {"expression": expression, "result": _eval_node(tree.body)}
    except (SyntaxError, ValueError, ZeroDivisionError) as exc:
        return {"expression": expression, "error": str(exc)}


# ---------------------------------------------------------------------------
# current_time — any IANA timezone
# ---------------------------------------------------------------------------


def current_time(timezone: str = "Africa/Lagos") -> dict[str, Any]:
    """Return the current date and time in a timezone such as 'Europe/Luxembourg'."""
    try:
        now = datetime.now(ZoneInfo(timezone))
    except ZoneInfoNotFoundError:
        return {"error": f"unknown timezone '{timezone}'"}
    return {"timezone": timezone, "iso": now.isoformat(timespec="seconds"), "weekday": now.strftime("%A")}


# ---------------------------------------------------------------------------
# get_weather — Open-Meteo (free, no API key)
# ---------------------------------------------------------------------------

_GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    full = f"{url}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(full, timeout=10) as resp:  # noqa: S310 (fixed https hosts)
        return json.loads(resp.read())


def get_weather(city: str) -> dict[str, Any]:
    """Current temperature, wind and conditions for a city."""
    try:
        geo = _get_json(_GEO_URL, {"name": city, "count": 1})
        if not geo.get("results"):
            return {"error": f"could not find city '{city}'"}
        place = geo["results"][0]
        data = _get_json(
            _WEATHER_URL,
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,wind_speed_10m,weather_code",
            },
        )
        cur = data["current"]
        return {
            "city": f"{place['name']}, {place.get('country', '')}".strip(", "),
            "temperature_c": cur["temperature_2m"],
            "wind_kmh": cur["wind_speed_10m"],
            "weather_code": cur["weather_code"],
        }
    except Exception as exc:  # network errors should not crash the agent
        return {"error": f"weather lookup failed: {exc}"}


# ---------------------------------------------------------------------------
# Registry: name -> (function, JSON schema)
# ---------------------------------------------------------------------------

TOOLS: dict[str, Callable[..., dict[str, Any]]] = {
    "calculator": calculator,
    "current_time": current_time,
    "get_weather": get_weather,
}

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate an arithmetic expression. Use for any maths instead of guessing.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "e.g. '(250000 * 0.075) + 1200'"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "current_time",
            "description": "Get the current date and time in an IANA timezone.",
            "parameters": {
                "type": "object",
                "properties": {"timezone": {"type": "string", "description": "e.g. 'Africa/Lagos', 'Europe/Luxembourg'"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "City name, e.g. 'Abuja'"}},
                "required": ["city"],
            },
        },
    },
]


def run_tool(name: str, arguments: str) -> str:
    """Run a tool by name with JSON-encoded arguments; always returns a JSON string."""
    func = TOOLS.get(name)
    if func is None:
        return json.dumps({"error": f"unknown tool '{name}'"})
    try:
        args = json.loads(arguments or "{}")
    except json.JSONDecodeError:
        return json.dumps({"error": "arguments were not valid JSON"})
    try:
        return json.dumps(func(**args))
    except TypeError as exc:
        return json.dumps({"error": f"bad arguments: {exc}"})
