# LEARN: Day 1 for a Laravel developer

This project is small on purpose. Here's what each piece is and how it maps to things you already know from Laravel.

## 1. Project setup

| Python                               | Laravel equivalent                     |
|--------------------------------------|----------------------------------------|
| `python -m venv .venv`               | a per-project `vendor/` folder         |
| `pip install -r requirements.txt`    | `composer install`                     |
| `requirements.txt`                   | `composer.json` (dependency list only) |
| `.env` + `python-dotenv`             | `.env` + `env()`                       |
| `pytest`                             | `php artisan test` / PHPUnit           |
| a folder with `__init__.py` (`agent/`) | a namespace (`App\Agent`)            |

`from agent.tools import run_tool` ≈ `use App\Agent\Tools;`

## 2. Python syntax you'll see here

```python
def calculator(expression: str) -> dict[str, Any]:
```
Type hints, like `function calculator(string $expression): array`. Python doesn't enforce them at runtime, but editors and tools check them.

```python
@dataclass
class Agent:
    client: Any
    model: str
    max_steps: int = 6
```
A `@dataclass` generates the constructor for you. It's like PHP 8 constructor promotion:
`public function __construct(public $client, public string $model, public int $maxSteps = 6) {}`

```python
{"role": "user", "content": user_input}
```
A `dict` is an associative array: `['role' => 'user', 'content' => $userInput]`.

```python
[tc.id for tc in tool_calls]
```
A list comprehension: `collect($toolCalls)->map(fn ($tc) => $tc->id)->all()`.

## 3. How the agent works (the important part)

An LLM can't run code. **Tool calling** is a contract:

1. We send the model the conversation **plus a list of tools** described as JSON Schema (`TOOL_SCHEMAS`). It's like giving it the API docs.
2. The model replies with either text or a request like `calculator({"expression": "84000*0.15"})`.
3. **We** run the function (`run_tool`) and append the result as a `role: "tool"` message.
4. We call the model again, and it now sees the result and can answer or ask for another tool.

That loop is in `agent/core.py`, `Agent.ask()`. In Laravel terms it's a `while` loop around an HTTP call, much like retrying a job until it has what it needs. `max_steps` is your `$tries`.

## 4. Why no `eval()`?

The model writes the calculator expression. If we passed it to `eval()`, a prompt-injected input could run `__import__('os').system(...)`. Instead we parse it into a syntax tree (`ast`) and allow only numbers and arithmetic operators. **Never trust model output**, just as you'd never trust user input without validation in a Form Request.

## 5. Testing without an API key

`tests/test_agent.py` builds a `FakeClient` that returns scripted replies. It's the same idea as `Http::fake()` in Laravel: test your logic, not the network.

## Try this

- Add a `currency_convert` tool, register it, and ask "What's $50 in naira?"
- Set `LLM_PROVIDER=groq` and compare speed with Gemini.
- Lower `max_steps` to 1 and see what happens on a two-tool question.
