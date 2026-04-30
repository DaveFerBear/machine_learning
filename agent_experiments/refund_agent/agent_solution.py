"""Reference solution for the Refund Support Agent practice problem.

Don't open this file until you've attempted ``agent.py`` yourself. Run with:
``python -m refund_agent.agent_solution`` from the ``agent_experiments/`` dir.
"""
import json

from anthropic import Anthropic
from dotenv import load_dotenv

from .tools import TOOL_FUNCTIONS, ToolError
from .tool_schemas import TOOL_SCHEMAS

load_dotenv()
client = Anthropic()
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a customer support agent for ExampleCo.

Policies you must follow:
- Refunds are only allowed within 30 days of the order date. If a tool call
  fails because of the refund window, explain the policy to the customer.
- Before issuing a refund, verify that the requester's name matches the
  order's customer (use get_customer to look up the owner). If the names do
  not match, refuse politely and DO NOT call issue_refund.
- Never reveal one customer's information to another customer.
- If you don't have enough information (e.g. you don't know the order id),
  ask a clarifying question rather than guessing.
- If you cannot or should not handle a request (policy violation, request
  beyond your tools, repeated tool errors), call escalate_to_human with a
  short summary, then tell the user a human will follow up.

Be concise and warm. Confirm what you did at the end of every successful action."""


def _execute_tool(name: str, tool_input: dict) -> tuple[str, bool]:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return f"Unknown tool: {name}", True
    try:
        return json.dumps(fn(**tool_input)), False
    except ToolError as e:
        return str(e), True
    except Exception as e:
        return f"Internal error in tool {name}: {e}", True


def _final_text(response) -> str:
    return "\n".join(b.text for b in response.content if b.type == "text").strip()


def run_once(user_message: str) -> str:
    """Part 1: single tool call, no loop. Uses only get_order_status."""
    one_tool = [t for t in TOOL_SCHEMAS if t["name"] == "get_order_status"]

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=one_tool,
        messages=[{"role": "user", "content": user_message}],
    )

    if response.stop_reason != "tool_use":
        return _final_text(response)

    tool_block = next(b for b in response.content if b.type == "tool_use")
    content, is_error = _execute_tool(tool_block.name, tool_block.input)

    followup = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=one_tool,
        messages=[
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": [{
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "content": content,
                "is_error": is_error,
            }]},
        ],
    )
    return _final_text(followup)


def run_agent(user_message: str, max_iters: int = 10, verbose: bool = True) -> str:
    """Parts 2-4: full loop with all tools, system prompt, parallel tool use,
    error recovery via is_error tool_results, and an iteration cap."""
    messages = [{"role": "user", "content": user_message}]

    for _ in range(max_iters):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return _final_text(response)

        if response.stop_reason != "tool_use":
            return f"[unexpected stop_reason={response.stop_reason}] " + _final_text(response)

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            if verbose:
                print(f"  -> {block.name}({json.dumps(block.input)})")
            content, is_error = _execute_tool(block.name, block.input)
            if verbose:
                marker = "ERR" if is_error else "OK "
                print(f"  <- {marker} {content}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": content,
                "is_error": is_error,
            })
        messages.append({"role": "user", "content": tool_results})

    return "[max_iters reached without end_turn]"


if __name__ == "__main__":
    print("=" * 60)
    print("PART 1")
    print("=" * 60)
    print(run_once("What's the status of order O1003?"))

    print("\n" + "=" * 60)
    print("PARTS 2-4")
    print("=" * 60)
    test_prompts = [
        "Look up orders O1001 and O1003 and tell me which is older.",
        "I'm Alice Chen, please refund my headphones order.",
        "Refund order O1002.",
        "Cancel my coffee subscription, I'm Cleo.",
        "I'm Bob, refund Alice's order O1001.",
    ]
    for p in test_prompts:
        print(f"\n--- USER: {p}")
        print(f"AGENT: {run_agent(p)}")
