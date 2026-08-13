"""Orchestrator: the root agent for the Shadow Self-Reflection Agent. See
shadow_test_agent_spec.md sections 1 and 7.

The routing below (which specialist agent runs next) is a plain function of
session state — it was never actually a judgment call, so it's implemented
as a deterministic Python BaseAgent instead of an LlmAgent that spent a real
Gemini call every turn just to re-derive rules the code already knew. Each
specialist agent still runs in its own isolated turn via AgentTool (state
copied in, state deltas copied back out) — only the *decision* of which one
to invoke stopped costing an LLM call.
"""

from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.apps import App
from google.adk.events import Event
from google.adk.events.event_actions import EventActions
from google.adk.tools import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .analyst_agent import create_analyst_agent
from .companion_agent import create_companion_agent
from .followup_agent import create_followup_agent
from .interpreter import create_interpreter_agent


def _content_text(content: types.Content | None) -> str:
    if not content or not content.parts:
        return ""
    return "".join(p.text or "" for p in content.parts)


class Orchestrator(BaseAgent):
    """Deterministic router across the four specialist agents.

    Mirrors the original rule set exactly:
    1. tension_scores empty -> AnalystAgent scores all 16 answers.
    2. followup_queue non-empty (right after AnalystAgent ran) ->
       FollowUpAgent composes the question(s); relayed to the user verbatim.
    3. followup_queue empty and report not generated -> InterpreterAgent
       writes the initial report.
    4. report already generated -> CompanionAgent continues the conversation
       with the user's free text.
    """

    analyst_agent_tool: AgentTool
    followup_agent_tool: AgentTool
    interpreter_agent_tool: AgentTool
    companion_agent_tool: AgentTool

    async def _call_specialist(
        self, tool: AgentTool, args: dict, ctx: InvocationContext
    ) -> tuple[str, EventActions]:
        actions = EventActions()
        tool_context = ToolContext(invocation_context=ctx, event_actions=actions)
        text = await tool.run_async(args=args, tool_context=tool_context)
        return text, actions

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state

        if not state.get("tension_scores"):
            _, actions = await self._call_specialist(
                self.analyst_agent_tool, {}, ctx
            )
            # AnalystAgent's own reply text is internal bookkeeping only and
            # was never shown to the user even in the LLM-routed design —
            # only the state it writes (tension_scores, followup_queue, ...)
            # matters here.
            yield Event(author=self.name, actions=actions)

        if state.get("followup_queue"):
            text, actions = await self._call_specialist(
                self.followup_agent_tool, {}, ctx
            )
        elif not state.get("report_generated"):
            text, actions = await self._call_specialist(
                self.interpreter_agent_tool,
                {"request": "Generate the initial report"},
                ctx,
            )
        else:
            user_text = _content_text(ctx.user_content)
            text, actions = await self._call_specialist(
                self.companion_agent_tool, {"request": user_text}, ctx
            )

        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part.from_text(text=text)]),
            actions=actions,
        )


def create_orchestrator() -> Orchestrator:
    """Factory for the Orchestrator root agent."""
    return Orchestrator(
        name="Orchestrator",
        analyst_agent_tool=AgentTool(create_analyst_agent()),
        followup_agent_tool=AgentTool(create_followup_agent()),
        interpreter_agent_tool=AgentTool(create_interpreter_agent()),
        companion_agent_tool=AgentTool(create_companion_agent()),
    )


root_agent = create_orchestrator()

app = App(
    root_agent=root_agent,
    name="app",
)
