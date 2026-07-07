"""AnalystAgent: a thin LlmAgent wrapping the deterministic analyst_tool, so
the Orchestrator calls it via AgentTool instead of holding the function tool
directly. See shadow_test_agent_spec_addendum.md section 1.
"""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from .tools import analyst_tool

ANALYST_INSTRUCTION = """
Your only job is to call analyst_tool to score the user's full answer set,
already present in session state under 'answers'. Do not compute or estimate
any scores yourself — all numbers must come from the tool's return value.
After calling the tool, reply with one short sentence summarizing which
shadow type showed the most tension. Do not explain the scoring method to
the user.
""".strip()


def create_analyst_agent() -> Agent:
    """Factory for AnalystAgent (called fresh per app, per adk-code guidance)."""
    return Agent(
        name="AnalystAgent",
        model=Gemini(
            model="gemini-flash-lite-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        description=(
            "Scores the user's 16 answers deterministically and identifies "
            "the shadow type(s) needing a follow-up question."
        ),
        instruction=ANALYST_INSTRUCTION,
        tools=[analyst_tool],
    )
