"""FollowUpAgent: composes a personalized clarifying question for every
shadow type currently queued, grounded in the user's actual answers to that
type's direct/projection pair — rather than picking from a fixed set of
canned templates, so wording and framing vary with what the person actually
answered instead of repeating the same phrasing every time.

AgentTool gives the wrapped agent a brand-new session on every call (state is
copied in, state deltas are copied back out) — there is no persistent
conversation history across calls.
"""

import re

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models import Gemini
from google.genai import types

from .shadow_data import SHADOW_PAIRS, get_questions

_FOLLOWUP_OUTPUT_KEY = "followup_last_output"

_LANGUAGE_NAMES = {"en": "English", "zh": "Simplified Chinese"}

# Parses "## <shadow_type>\nPROMPT: ...\nA: ...\nB: ..." blocks, one per
# queued type, in the order the model wrote them.
_BLOCK_RE = re.compile(
    r"##\s*(\S+)\s*\n"
    r"PROMPT:\s*(.+?)\s*\n"
    r"A:\s*(.+?)\s*\n"
    r"B:\s*(.+?)\s*(?=\n##|\Z)",
    re.DOTALL,
)


def _build_instruction(readonly_context: ReadonlyContext) -> str:
    """Built fresh each turn: embeds exactly the queued types' own
    direct/projection questions and the user's actual answers to them, so
    the model has the specific material to personalize each question from.
    """
    language = readonly_context.state.get("language", "en")
    language_name = _LANGUAGE_NAMES.get(language, "English")
    questions = get_questions(language)

    queue = readonly_context.state.get("followup_queue") or []
    answers = readonly_context.state.get("answers") or {}

    type_blocks = []
    for shadow_type in queue:
        direct_id, projection_id = SHADOW_PAIRS[shadow_type]
        type_blocks.append(
            f'- {shadow_type}:\n'
            f'    direct ("{questions[direct_id]["text"]}") -> answered {answers.get(direct_id)}/5\n'
            f'    projection ("{questions[projection_id]["text"]}") -> answered {answers.get(projection_id)}/5'
        )
    type_lines = "\n".join(type_blocks)
    queue_list = ", ".join(queue)

    return f"""
You are FollowUpAgent. For each shadow type below, write ONE short
clarifying question (plus exactly two answer options) that surfaces the
contradiction in how this specific person answered: a low score on the
direct item paired with a high score on the projection item means they may
be denying a trait in themselves while judging it in others. Ground the
question in what their answers reveal — do not use a generic, interchangeable
phrasing. Vary your sentence structure and tone between questions and
between sessions; do not default to the same template sentence every time.

Write it as a smooth, natural observation, the way a warm conversation
partner would put it — never cite the raw numbers or scores themselves
(e.g. do not write things like "(scored 1/5)" or "(q3=5)"). Translate what
the numbers mean into plain language instead (e.g. a flat rejection of one
idea alongside strong agreement with its opposite), not the numbers
themselves.

Shadow types needing a question, ranked highest-tension first:
{type_lines}

Option A should lean toward acknowledging the hidden/denied feeling.
Option B should lean toward maintaining the defended/surface stance.
Neither option is "correct" — keep both genuinely plausible, written in
first person, one to two sentences each.

Write everything in {language_name}.

Output ONLY the following, with no extra commentary before, after, or
between blocks — one block per type above, in this exact order:
{queue_list}

For each type, output exactly this structure (the "## <type>" line must use
the literal type identifier shown above, unchanged, not translated):

## <type>
PROMPT: <the clarifying question>
A: <option a>
B: <option b>
""".strip()


def _promote_followups(callback_context: CallbackContext) -> None:
    """Parses the "## type / PROMPT / A / B" blocks into a list of
    {shadow_type, prompt, option_a, option_b} dicts, ordered to match
    followup_queue, and writes it to followup_details — which, like other
    state writes, is forwarded back through AgentTool regardless of nesting,
    unlike trace/events.
    """
    raw = callback_context.state.get(_FOLLOWUP_OUTPUT_KEY) or ""
    parsed = {
        match.group(1).strip(): {
            "prompt": match.group(2).strip(),
            "option_a": match.group(3).strip(),
            "option_b": match.group(4).strip(),
        }
        for match in _BLOCK_RE.finditer(raw)
    }
    queue = callback_context.state.get("followup_queue") or []
    callback_context.state["followup_details"] = [
        {"shadow_type": t, **parsed[t]} for t in queue if t in parsed
    ]


def create_followup_agent() -> Agent:
    """Factory for FollowUpAgent (called fresh per app, per adk-code guidance)."""
    return Agent(
        name="FollowUpAgent",
        model=Gemini(
            model="gemini-flash-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        description=(
            "Composes a personalized clarifying question for every shadow "
            "type in followup_queue, grounded in the user's actual answers."
        ),
        instruction=_build_instruction,
        output_key=_FOLLOWUP_OUTPUT_KEY,
        after_agent_callback=_promote_followups,
    )
