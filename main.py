"""Interactive terminal chat with a tool-calling agent.

Usage:
    python main.py                       # interactive chat
    python main.py "What's 15% of 84,000?"   # one-shot question
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv
from rich.console import Console

from agent import Agent
from agent.providers import make_client

console = Console()


def show_tool_call(name: str, arguments: str, result: str) -> None:
    console.print(f"  [dim]🔧 {name}({arguments}) → {result}[/dim]")


def main() -> None:
    load_dotenv()
    client, model = make_client()
    agent = Agent(client=client, model=model, on_tool_call=show_tool_call)

    if len(sys.argv) > 1:
        console.print(agent.ask(" ".join(sys.argv[1:])))
        return

    console.print(f"[bold green]Tool agent[/bold green] using [cyan]{model}[/cyan]. Type 'exit' to quit.\n")
    while True:
        try:
            user_input = console.input("[bold]you › [/bold]").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in {"exit", "quit"}:
            break
        if user_input:
            console.print(f"[bold blue]agent ›[/bold blue] {agent.ask(user_input)}\n")


if __name__ == "__main__":
    main()
