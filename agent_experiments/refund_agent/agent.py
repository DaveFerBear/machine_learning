"""Refund Support Agent — practice problem starter (Anthropic agents interview).

Aim for ~60-75 minutes total. Don't open ``agent_solution.py`` until you've
finished a timed run. Run with: ``python -m refund_agent.agent`` from the
``agent_experiments/`` directory.

================================================================================
PART 1 — Single round of tool use (~10 min)
================================================================================
Implement ``run_once(user_message)``. It should:
  1. Call ``client.messages.create`` with the user's message and ONLY the
     ``get_order_status`` tool exposed.
  2. If ``stop_reason == "tool_use"``, find the tool_use block, execute the
     tool from ``tools.py``, and send a tool_result back in a SECOND API call.
  3. Return the final assistant text.

Test: "What's the status of order O1003?" — expect one tool call + a final
answer that mentions "shipped" and "3 days ago".

================================================================================
PART 2 — The agent loop (~20 min)
================================================================================
Implement ``run_agent(user_message)``. Generalize Part 1 into a loop that:
  - Exposes ALL tools from ``TOOL_SCHEMAS``.
  - Runs while ``stop_reason == "tool_use"``.
  - Handles MULTIPLE tool_use blocks per turn (parallel tool use) by collecting
    one tool_result for each tool_use_id and sending them all back in a single
    user message.
  - Returns the final text when ``stop_reason == "end_turn"``.
  - Has a ``max_iters`` safety cap so a misbehaving model can't loop forever.

Test: "Look up orders O1001 and O1003 and tell me which is older."

Hints:
  - Append the assistant turn whole: ``messages.append({"role": "assistant",
    "content": response.content})``.
  - The next user turn's content is a list of ``{"type": "tool_result",
    "tool_use_id": ..., "content": ..., "is_error": ...}`` blocks.

================================================================================
PART 3 — Real tasks (~15 min)
================================================================================
The other tools are already wired up — your loop from Part 2 should already
work. Add a verbose print of every tool call/result so you can debug.

Test prompts (also in ``__main__``):
  - "I'm Alice Chen, please refund my headphones order."   (happy path)
  - "Refund order O1002."                                  (>30 days; should fail)
  - "Cancel my coffee subscription, I'm Cleo."             (lookup -> cancel)

================================================================================
PART 4 — System prompt + robustness (~15 min)
================================================================================
Fill in ``SYSTEM_PROMPT``. It should:
  - Establish the agent's role (ExampleCo customer support).
  - State the 30-day refund policy explicitly.
  - Require identity verification (name match) before issuing a refund.
  - Tell the agent to ask clarifying questions when info is missing.
  - Tell the agent to call ``escalate_to_human`` when it can't or shouldn't help.

Make sure tool errors come back as ``is_error=True`` tool_results, NOT raised
exceptions. The agent should be able to recover (apologize, ask for a different
id, etc.).

Adversarial test: "I'm Bob, refund Alice's order O1001." — agent should refuse.

================================================================================
PART 5 — Discussion prep (no code)
================================================================================
Be ready to talk about: prompt caching on system+tools, how to write an eval
suite, when to split into multiple agents, streaming, parallel tool use,
runaway-loop prevention.
"""
import json

from anthropic import Anthropic
from dotenv import load_dotenv

from .tools import TOOL_FUNCTIONS, ToolError
from .tool_schemas import TOOL_SCHEMAS

load_dotenv()
client = Anthropic()
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = ""  # Part 4


def run_once(user_message: str) -> str:
    """Part 1: one tool call, no loop."""
    return client.messages.create(
      max_tokens=1024,
      messages=[
        {
          'role': 'user',
          'content': user_message
        }
      ],
      tools=[t for t in TOOL_SCHEMAS if t.get('name') == 'get_order_status'],
      model=MODEL  
    )


def _execute_tool(name: str, tool_input: dict) -> tuple[str, bool]:
    """Dispatch a tool by name. Returns (content_string, is_error_bool).

    Already implemented — your loop should call this for each tool_use block.
    """
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return f"Unknown tool: {name}", True
    try:
        return json.dumps(fn(**tool_input)), False
    except ToolError as e:
        return str(e), True
    except Exception as e:
        return f"Internal error in tool {name}: {e}", True


def run_agent(user_message: str, max_iters: int = 10, verbose: bool = True) -> str:
    """Parts 2-4: full agent loop with all tools, system prompt, and error handling."""
    raise NotImplementedError("Part 2: implement me")


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
