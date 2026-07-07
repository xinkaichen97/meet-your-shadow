"""CompanionAgent: continues the reflective conversation after the report has
been generated. Split out from InterpreterAgent so each agent has one job —
InterpreterAgent writes the report once; CompanionAgent only ever talks
about it afterward, with its own narrower, tone-focused instruction.

AgentTool gives the wrapped agent a brand-new session on every call, so
there's no persistent conversation history across calls — continuity comes
from reading {final_report} back out of state, not from chat history.
"""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

COMPANION_INSTRUCTION = """
You are CompanionAgent. The report has already been written by
InterpreterAgent; your only job is to continue that conversation when the
user sends free text afterward.

Current session state:
- final_report (the narrative already shown to the user): {final_report}

Read final_report for continuity of voice and content. Respond to the
user's message as a continuation of the same conversation — same tone, same
restraint, and UNDER 100 WORDS, as one short passage. Do not repeat the
report. Do not introduce new diagnostic claims beyond what was already
established in final_report. If the user asks "what should I do," gently
decline to prescribe a fix and instead reflect the question back with care.

Never rush the user, never use words like "should" or "must," and keep
responses grounded in what the user has actually said — do not invent
details they didn't provide.
""".strip()


def create_companion_agent() -> Agent:
    """Factory for CompanionAgent (called fresh per app, per adk-code guidance)."""
    return Agent(
        name="CompanionAgent",
        model=Gemini(
            model="gemini-flash-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        description=(
            "Continues the reflective conversation after the report has "
            "been generated. Call with request set to the user's free-text "
            "message, verbatim."
        ),
        instruction=COMPANION_INSTRUCTION,
    )
