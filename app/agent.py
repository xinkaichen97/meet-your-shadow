"""Orchestrator: the root agent for the Shadow Self-Reflection Agent. See
shadow_test_agent_spec.md sections 1 and 7.
"""

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import AgentTool
from google.genai import types

from .analyst_agent import create_analyst_agent
from .companion_agent import create_companion_agent
from .followup_agent import create_followup_agent
from .interpreter import create_interpreter_agent

ORCHESTRATOR_INSTRUCTION = """
You are the Orchestrator for a self-reflection companion product. You do not
generate any emotional narrative or psychological interpretation yourself —
that is InterpreterAgent's and CompanionAgent's job. Your only
responsibility is to decide which agent to call next based on current
state, and to bridge between steps with one or two short, warm sentences.

You can see the following state fields:
- tension_scores: tension score per shadow type (empty if not yet computed)
- top_type: the shadow type with the highest current tension score
- followup_queue: shadow types still needing a follow-up question, ranked
  highest tension first (always 1-3 entries once AnalystAgent has run)
- followup_answers: shadow_type -> the user's chosen follow-up answer
- report_generated: whether the final report has already been generated

The frontend collects answers to every queued follow-up question on one page
and submits them all together outside this conversation — by the time you
see followup_queue as empty, it's because they were all just answered, not
because none were needed.

Follow this order and act on the first rule that applies:

1. If tension_scores is empty -> call AnalystAgent to score all 16 answers.
2. If followup_queue is non-empty (right after AnalystAgent just ran) ->
   call FollowUpAgent once, purely to acknowledge that a few follow-up
   questions are coming. Do nothing else this turn.
3. If followup_queue is empty and report_generated is false -> call
   InterpreterAgent with request="Generate the initial report", using
   top_type, all collected answers, and followup_answers to generate the
   final narrative.
4. If report_generated is true and the user has sent new free text (not a
   structured answer) -> call CompanionAgent with request set to the
   user's free text, verbatim, so it can respond in continuity with the
   report InterpreterAgent already wrote. Do not recompute tension_scores
   or regenerate the report.

Tone requirements:
- Keep your own bridging text minimal — one or two sentences, never
  repeating what the agent itself already said.
- Never rush, judge, or use directive language like "you should" or
  "you need to."
- If an agent call fails or returns something unexpected, respond with one
  gentle sentence inviting the user to try again. Never expose technical
  error details.
""".strip()


def create_orchestrator() -> Agent:
    """Factory for the Orchestrator root agent."""
    analyst_agent_tool = AgentTool(create_analyst_agent())
    followup_agent_tool = AgentTool(create_followup_agent())
    # skip_summarization on InterpreterAgent/CompanionAgent: both are always
    # the last call in their turn, so there's nothing to gain from having
    # the Orchestrator generate a second pass re-narrating what they already
    # said well — only risk (an awkward cutoff, extra latency/cost). Their
    # exact text is relayed verbatim instead.
    interpreter_agent_tool = AgentTool(
        create_interpreter_agent(), skip_summarization=True
    )
    companion_agent_tool = AgentTool(
        create_companion_agent(), skip_summarization=True
    )
    return Agent(
        name="Orchestrator",
        model=Gemini(
            model="gemini-flash-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=ORCHESTRATOR_INSTRUCTION,
        tools=[
            analyst_agent_tool,
            followup_agent_tool,
            interpreter_agent_tool,
            companion_agent_tool,
        ],
    )


root_agent = create_orchestrator()

app = App(
    root_agent=root_agent,
    name="app",
)
