"""FollowUpAgent: a thin LlmAgent wrapping the deterministic followup_tool, so
the Orchestrator calls it via AgentTool instead of holding the function tool
directly. See shadow_test_agent_spec_addendum.md section 2.

Recording the user's answer (record_followup_answer) stays a direct
Orchestrator-level tool — the addendum only asks to wrap the
question-presenting half, and folding recording in here too would add an
extra LLM hop to a step that's purely bookkeeping.
"""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from .tools import followup_tool

FOLLOWUP_INSTRUCTION = """
Call followup_tool to get the next pending follow-up question. Present the
returned prompt and both options to the user exactly as written — do not
paraphrase or reword option_a or option_b, their exact wording matters for
later interpretation. You may add one short, warm sentence before presenting
the question, nothing more.
""".strip()


def create_followup_agent() -> Agent:
    """Factory for FollowUpAgent (called fresh per app, per adk-code guidance)."""
    return Agent(
        name="FollowUpAgent",
        model=Gemini(
            model="gemini-flash-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        description="Presents the fixed clarifying question for the next queued shadow type.",
        instruction=FOLLOWUP_INSTRUCTION,
        tools=[followup_tool],
    )
