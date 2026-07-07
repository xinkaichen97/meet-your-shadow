"""Deterministic (non-LLM) building blocks: AnalystTool, FollowUpTool, and
record_answers. See shadow_test_agent_spec.md sections 2, 4, 5.
"""

from google.adk.tools import ToolContext

from .shadow_data import FOLLOWUP_TEMPLATES, SHADOW_PAIRS


def record_answers(answers: dict, state: dict) -> dict:
    """Writes a freshly submitted 16-answer batch into session state.

    Plain function, no LLM involved. Called by the backend (outside the
    Runner/Orchestrator loop) when the frontend submits all 16 answers,
    before the Orchestrator's first turn for this session.
    """
    state["answers"] = answers
    state["tension_scores"] = {}
    state["top_type"] = None
    state["followup_queue"] = []
    state["followup_answers"] = {}
    state["report_generated"] = False
    state["final_report"] = None
    return state


def analyst_tool(tool_context: ToolContext) -> dict:
    """Scores the user's 16 answers to find shadow-type tension.

    For each shadow type, combines how strongly the direct item was denied
    (a low score) with how strongly the same trait was projected onto others
    (a high score) into a single tension_score. The highest-tension type
    always gets a follow-up question; the 2nd and 3rd highest also get one
    if they independently trip the same denial/projection trigger — so
    followup_queue always has 1-3 entries, ranked highest tension first.

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

    followup_queue = [top_type]
    for candidate in ranked[1:3]:
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


def followup_tool(tool_context: ToolContext) -> dict:
    """Looks up the fixed follow-up question for the next queued shadow type.

    Deterministic template lookup, no LLM generation. Neither option is
    framed as more "correct" than the other. Peeks the front of
    followup_queue without removing it — record_followup_batch does that
    once the user actually answers (via a dedicated endpoint, not this tool).

    Also writes the payload to session state under current_followup: since
    FollowUpTool now runs inside its own AgentTool-wrapped agent, this
    function's return value is only visible to that sub-agent's own LLM
    turn — the Orchestrator (and the frontend) never sees this dict
    directly, only whatever prose the sub-agent writes based on it. State
    writes, unlike tool call/response events, are forwarded back through
    AgentTool regardless of nesting, so current_followup is the reliable
    channel for the frontend to render exact option text.

    Returns:
        dict with status, shadow_type, prompt, option_a, and option_b.
    """
    queue = tool_context.state.get("followup_queue", [])
    if not queue:
        return {"status": "error", "message": "No follow-up question pending."}

    current_type = queue[0]
    template = FOLLOWUP_TEMPLATES[current_type]
    payload = {
        "status": "success",
        "shadow_type": current_type,
        "prompt": template["prompt"],
        "option_a": template["option_a"],
        "option_b": template["option_b"],
    }
    tool_context.state["current_followup"] = payload
    return payload


def record_followup_batch(answers: dict, state: dict) -> dict:
    """Records answers to every currently pending follow-up question at once.

    Plain function, no LLM involved. The frontend now shows all queued
    follow-up questions on a single page and submits them together, so
    there's no per-question chaining through the Orchestrator anymore —
    this runs directly against the session's state dict (mirroring
    record_answers) before the next Runner turn starts, clearing
    followup_queue entirely.
    """
    queue = list(state.get("followup_queue", []))
    followup_answers = dict(state.get("followup_answers", {}))

    for shadow_type in queue:
        if shadow_type in answers:
            followup_answers[shadow_type] = answers[shadow_type]

    state["followup_queue"] = []
    state["followup_answers"] = followup_answers
    state["current_followup"] = None
    return state
