"""Deterministic (non-LLM) building blocks: AnalystTool and record_answers.
See shadow_test_agent_spec.md sections 2, 4, 5.
"""

from google.adk.tools import ToolContext

from .shadow_data import SHADOW_PAIRS


def record_answers(answers: dict, state: dict, language: str = "en") -> dict:
    """Writes a freshly submitted 16-answer batch into session state.

    Plain function, no LLM involved. Called by the backend (outside the
    Runner/Orchestrator loop) when the frontend submits all 16 answers,
    before the Orchestrator's first turn for this session. language ("en" or
    "zh") is stored in state so every agent's instruction can read it back
    for the rest of the session.
    """
    state["answers"] = answers
    state["language"] = language
    state["tension_scores"] = {}
    state["top_type"] = None
    state["followup_queue"] = []
    state["followup_answers"] = {}
    state["followup_details"] = None
    state["report_generated"] = False
    state["final_report"] = None
    return state


def analyst_tool(tool_context: ToolContext) -> dict:
    """Scores the user's 16 answers to find shadow-type tension.

    For each shadow type, combines how strongly the direct item was denied
    (a low score) with how strongly the same trait was projected onto others
    (a high score) into a single tension_score. A follow-up question is only
    warranted when a type shows a genuine denial/projection conflict (direct
    <= 2 and projection >= 4) — top_type does NOT automatically get one just
    for ranking highest; a mild top_type with no real conflict shouldn't be
    interrogated further. Checks the top 3 ranked types, so followup_queue
    can be empty (no real conflict at all) up to 3 entries, ranked highest
    tension first.

    Returns:
        dict with status, tension_scores, top_type, and followup_count.
    """
    answers = tool_context.state.get("answers", {})

    tension_scores = {}
    for shadow_type, (direct_id, projection_id) in SHADOW_PAIRS.items():
        direct_score = answers[direct_id]
        projection_score = answers[projection_id]
        denial_strength = 6 - direct_score
        projection_strength = projection_score
        tension_scores[shadow_type] = denial_strength + projection_strength

    ranked = sorted(tension_scores, key=tension_scores.get, reverse=True)
    top_type = ranked[0]

    followup_queue = []
    for candidate in ranked[:3]:
        direct_id, projection_id = SHADOW_PAIRS[candidate]
        if answers[direct_id] <= 2 and answers[projection_id] >= 4:
            followup_queue.append(candidate)

    tool_context.state["tension_scores"] = tension_scores
    tool_context.state["top_type"] = top_type
    tool_context.state["followup_queue"] = followup_queue
    tool_context.state["followup_answers"] = {}

    return {
        "status": "success",
        "tension_scores": tension_scores,
        "top_type": top_type,
        "followup_count": len(followup_queue),
    }


def record_followup_batch(current_state: dict, answers: dict) -> dict:
    """Computes the state delta for recording every currently pending
    follow-up answer at once.

    Plain function, no LLM involved. Returns a delta dict meant to be passed
    as Runner.run_async's `state_delta` argument for the next turn — NOT
    applied by mutating a session fetched via get_session() directly: ADK's
    session services return a detached copy from get_session(), so mutating
    its .state has no effect on canonical storage. state_delta is the
    sanctioned way to inject state changes before a turn starts.

    current_state: a read-only snapshot (e.g. from get_session()) used only
    to read the existing followup_queue/followup_answers to merge into.
    """
    queue = list(current_state.get("followup_queue", []))
    followup_answers = dict(current_state.get("followup_answers", {}))

    for shadow_type in queue:
        if shadow_type in answers:
            followup_answers[shadow_type] = answers[shadow_type]

    return {
        "followup_queue": [],
        "followup_answers": followup_answers,
        "followup_details": None,
    }
