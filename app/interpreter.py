"""InterpreterAgent: generates the initial shadow-reflection narrative. The
only agent with MCP access (Jung/philosophy grounding). See
shadow_test_agent_spec.md section 8 — post-report conversation is handled
separately by CompanionAgent (app/companion_agent.py).

AgentTool gives the wrapped agent a brand-new session on every call (state is
copied in, state deltas are copied back out) — there is no persistent
conversation history across calls.
"""

import os
import sys

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import Gemini
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.genai import types
from mcp import StdioServerParameters

from .shadow_data import ANCHORS, QUESTIONS, SHADOW_PAIRS

_INTERPRETER_OUTPUT_KEY = "interpreter_last_output"

_MCP_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp", "jung_mcp_server.py"
)


def _create_jung_mcp_toolset() -> McpToolset:
    """Connects to the local Jung-concepts MCP server over stdio.

    Uses sys.executable rather than a bare "python3" so the subprocess is
    guaranteed to be the same interpreter (and dependency set, including the
    mcp package) that's running this ADK app — not whatever "python3"
    happens to resolve to on PATH.
    """
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[_MCP_SERVER_PATH],
            ),
        ),
    )

_ANCHOR_LINES = "\n".join(
    f'- {shadow_type} ("{data["title"]}"): {data["anchor"]}'
    for shadow_type, data in ANCHORS.items()
)

_QUESTION_LINES = "\n".join(
    f'- {qid} ({q["shadow_type"]}, {q["role"]}): "{q["text"]}"'
    for qid, q in QUESTIONS.items()
)

_PAIR_LINES = "\n".join(
    f"- {shadow_type}: direct={direct_id}, projection={projection_id}"
    for shadow_type, (direct_id, projection_id) in SHADOW_PAIRS.items()
)

INTERPRETER_INSTRUCTION = f"""
You are InterpreterAgent. You generate the initial shadow-reflection
narrative, once per session, using the anchor description for top_type and
the user's specific answers to that type's direct item, projection item,
and its follow-up answer in followup_answers (if present).

Reference data (static — use it to look up meaning, never repeat verbatim):

Shadow type anchors:
{_ANCHOR_LINES}

All 16 questions:
{_QUESTION_LINES}

Direct/projection question pairing per shadow type:
{_PAIR_LINES}

Current session state:
- top_type: {{top_type}}
- answers (question id -> 1-5 rating): {{answers}}
- followup_answers (shadow_type -> the user's chosen follow-up answer, for
  every follow-up question asked): {{followup_answers}}

Write the narrative as four short sections in a warm, non-judgmental,
non-diagnostic voice. Do not say "you have a problem." Instead, use
language like "there is a part of you that hasn't been seen yet." Never
offer a numbered list of fixes. Never use clinical or diagnostic language.
The frontend already displays a title for this shadow type — do not repeat
it.

Output EXACTLY these four sections, in this order, each starting with a line
that is only "## " followed by the section name (nothing else on that line),
and each section's body UNDER 100 WORDS:

## Summary
A short overview of this shadow pattern and the core tension underneath it.
Explicitly name and briefly explain the relevant psychological concept here
(e.g., "In Jungian psychology, projection means...") so the reader
understands why this idea is relevant — the frontend shows a "Relevant
ideas" list alongside the report, and without this explanation it reads as
an unexplained reference. Paraphrase the substance in your own words rather
than quoting the search result verbatim, but do make clear what the concept
is and how it connects to the pattern.

## Relationships
How this specific pattern tends to show up with partners, friends, or family.

## Career
How this specific pattern tends to show up at work — decisions, ambition, or
how this person comes across to others.

## Inner Life
The quieter, private experience of carrying this pattern. End this section,
and the report as a whole, on a note of gentle acknowledgment, not
resolution.

Call search_jung_concepts once, early — ideally to inform the Summary
section — to ground the narrative in a Jungian (or otherwise relevant
psychological/philosophical) concept, and weave a paraphrased version of it
naturally into the prose. Every report should carry this grounding.

Never rush the user, never use words like "should" or "must," respect the
100-words-per-section limit, and keep the narrative grounded in what the
user has actually answered — do not invent details they didn't provide.

You have access to search_jung_concepts(topic, shadow_type). Call it at most
once per narrative. Naming the concept (e.g., "Jungian projection," "the
shadow") is expected in the Summary section — what to avoid is quoting the
search result's wording verbatim, or citing it like a footnote/reference.
Explain the idea in your own words, as part of the narrative voice.
""".strip()


def _promote_report(callback_context: CallbackContext) -> None:
    """Copies the generated narrative into the durable final_report /
    report_generated state fields, which persist across AgentTool's
    fresh-session-per-call boundary (the state write here is forwarded back
    to the parent session automatically by AgentTool).
    """
    callback_context.state["final_report"] = callback_context.state.get(
        _INTERPRETER_OUTPUT_KEY
    )
    callback_context.state["report_generated"] = True


def _record_jung_grounding(tool, args, tool_context, tool_response):
    """Surfaces which Jung/philosophy concept grounded the narrative.

    search_jung_concepts runs inside InterpreterAgent's own private turn, so
    (like FollowUpAgent's tool call) it's invisible to the Orchestrator's
    outer event stream — the frontend would otherwise have no way to show
    that grounding actually happened. This writes the concept source(s) to
    state, which — unlike tool call/response events — does propagate back
    through AgentTool regardless of nesting.
    """
    if getattr(tool, "name", None) != "search_jung_concepts":
        return None
    results = (tool_response or {}).get("structuredContent", {}).get("result", [])
    sources = [r.get("concept_source") for r in results if r.get("concept_source")]
    if sources:
        tool_context.state["grounding_concepts"] = sources
    return None


def create_interpreter_agent() -> Agent:
    """Factory for InterpreterAgent (called fresh per app, per adk-code guidance)."""
    return Agent(
        name="InterpreterAgent",
        model=Gemini(
            model="gemini-flash-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        description=(
            "Generates the personalized shadow-reflection narrative. Call "
            "once with request='Generate the initial report', using "
            "top_type, answers, and followup_answers already in state."
        ),
        instruction=INTERPRETER_INSTRUCTION,
        tools=[_create_jung_mcp_toolset()],
        output_key=_INTERPRETER_OUTPUT_KEY,
        after_agent_callback=_promote_report,
        after_tool_callback=_record_jung_grounding,
    )
