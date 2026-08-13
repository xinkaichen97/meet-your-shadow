# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib
import json
import os
import re
import uuid
from collections.abc import AsyncGenerator, AsyncIterator

import google.auth
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.cloud import logging as google_cloud_logging
from google.genai import types
from pydantic import BaseModel

from app.app_utils import services
from app.app_utils.a2a import attach_a2a_routes
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback
from app.crisis import get_crisis_response, is_crisis_text
from app.interpreter import _SECTION_NAMES
from app.shadow_data import get_anchors
from app.tools import record_answers, record_followup_batch
from app.translator_agent import create_translator_agent

load_dotenv()
setup_telemetry()
_, project_id = google.auth.default()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from app.agent import app as adk_app
    from app.agent import root_agent

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,
    )
    app.state.runner = runner
    app.state.agent_app_name = adk_app.name
    await attach_a2a_routes(
        app,
        agent=root_agent,
        runner=runner,
        task_store=InMemoryTaskStore(),
        rpc_path=f"/a2a/{adk_app.name}",
    )
    yield


app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    allow_origins=allow_origins,
    session_service_uri=services.SESSION_SERVICE_URI,
    otel_to_cloud=False,
    lifespan=lifespan,
)
app.title = "shadow-agent"
app.description = "API for interacting with the Agent shadow-agent"


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


# --- Shadow Self-Reflection Agent: frontend + agent-driven-step endpoints ---
# See shadow_test_agent_spec.md sections 1, 9, 11.

_USER_ID = "local"


class AnswersRequest(BaseModel):
    answers: dict[str, int]
    language: str = "en"


class MessageRequest(BaseModel):
    session_id: str
    text: str
    language: str = "en"


class FollowupBatchRequest(BaseModel):
    session_id: str
    answers: dict[str, str]
    language: str = "en"


class TranslateReportRequest(BaseModel):
    report: str
    target_language: str


_LANGUAGE_NAMES = {"en": "English", "zh": "Simplified Chinese"}
_SECTION_RE = re.compile(r"##\s*(.+?)\s*\n([\s\S]*?)(?=\n##|\Z)")
_NUMBERED_ITEM_RE = re.compile(r"^\s*\d+\.\s*(.*)$")


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj)}\n\n"


async def _translate_items(items: list[str], target_language: str) -> list[str]:
    """One-shot literal translation of a list of short text items via a
    throwaway agent/session — for content generated earlier in another
    language, not a full regeneration. Falls back to the originals if the
    model's output doesn't line up item-for-item, rather than risk silently
    misaligning translated text with the wrong item.
    """
    if not items:
        return []
    language_name = _LANGUAGE_NAMES.get(target_language, "English")
    agent = create_translator_agent(language_name)
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="translate", user_id=_USER_ID)
    runner = Runner(agent=agent, app_name="translate", session_service=session_service)

    prompt = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))
    content = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    reply = ""
    async for event in runner.run_async(
        user_id=_USER_ID, session_id=session.id, new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            reply = "".join(p.text or "" for p in event.content.parts)

    lines = [line for line in reply.strip().split("\n") if line.strip()]
    translated = [
        (m.group(1) if (m := _NUMBERED_ITEM_RE.match(line)) else line) for line in lines
    ]
    return translated if len(translated) == len(items) else items


async def _stream_turn(
    session_id: str, text: str, state_delta: dict | None = None
) -> AsyncGenerator[dict, None]:
    """Sends one message through the Orchestrator, then yields a final dict
    with the reply and the session state fields the frontend needs to decide
    what to render next.

    state_delta is applied atomically as part of starting this turn — NOT by
    mutating a session fetched via get_session() beforehand, since ADK's
    session services return a detached copy from get_session() and mutating
    its .state silently never reaches canonical storage.
    """
    runner: Runner = app.state.runner
    content = types.Content(role="user", parts=[types.Part.from_text(text=text)])
    reply_parts: list[str] = []

    async for event in runner.run_async(
        user_id=_USER_ID,
        session_id=session_id,
        new_message=content,
        state_delta=state_delta,
    ):
        # AnalystAgent's own event carries a followup_queue delta. An empty
        # one means no real conflict was found, so the Orchestrator is about
        # to go straight to InterpreterAgent this turn — tell the frontend
        # so it can swap its wait-screen text before the report itself is
        # ready (which is a separate, later event).
        delta = event.actions.state_delta if event.actions else {}
        if "followup_queue" in delta and not delta["followup_queue"]:
            yield {"type": "phase", "phase": "report"}
        if event.is_final_response() and event.content and event.content.parts:
            text = "".join(p.text or "" for p in event.content.parts)
            if text:
                reply_parts.append(text)

    session = await runner.session_service.get_session(
        app_name=app.state.agent_app_name, user_id=_USER_ID, session_id=session_id
    )
    state = session.state if session else {}
    top_type = state.get("top_type")
    anchors = get_anchors(state.get("language", "en"))
    yield {
        "type": "final",
        "reply": "\n".join(reply_parts),
        "top_type": top_type,
        "top_type_title": anchors.get(top_type, {}).get("title") if top_type else None,
        "followup_queue": state.get("followup_queue", []),
        "followup_details": state.get("followup_details"),
        "report_generated": state.get("report_generated"),
        "final_report": state.get("final_report"),
        "grounding_concepts_en": state.get("grounding_concepts_en"),
        "grounding_concepts_zh": state.get("grounding_concepts_zh"),
    }


@app.post("/api/answers")
async def submit_answers(req: AnswersRequest) -> StreamingResponse:
    """Seeds a new session from a submitted 16-answer batch, then streams the
    Orchestrator's first turn (analyst -> acknowledge follow-ups, or report)."""
    session_id = str(uuid.uuid4())
    initial_state = record_answers(req.answers, {}, req.language)
    await app.state.runner.session_service.create_session(
        app_name=app.state.agent_app_name,
        user_id=_USER_ID,
        session_id=session_id,
        state=initial_state,
    )

    async def gen():
        async for chunk in _stream_turn(session_id, "Here are my answers."):
            if chunk["type"] == "final":
                chunk["session_id"] = session_id
            yield _sse(chunk)

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/api/message")
async def send_message(req: MessageRequest) -> StreamingResponse:
    """Free-text chat (post-report conversation) comes through here. Crisis
    keywords are checked before the Runner is ever invoked, per spec section 9.
    """
    if is_crisis_text(req.text):

        async def crisis_gen():
            yield _sse(
                {
                    "type": "final",
                    "session_id": req.session_id,
                    "reply": get_crisis_response(req.language),
                    "crisis": True,
                }
            )

        return StreamingResponse(crisis_gen(), media_type="text/event-stream")

    async def gen():
        # Language delta applied atomically as this turn starts, in case the
        # user switched it since the session started — CompanionAgent reads
        # it fresh each turn.
        async for chunk in _stream_turn(
            req.session_id, req.text, state_delta={"language": req.language}
        ):
            if chunk["type"] == "final":
                chunk["session_id"] = req.session_id
            yield _sse(chunk)

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/api/followup-batch")
async def submit_followup_batch(req: FollowupBatchRequest) -> StreamingResponse:
    """Records every pending follow-up answer at once (deterministic, no LLM),
    then streams the next Orchestrator turn — which will find followup_queue
    already empty and move straight to report generation.
    """
    session = await app.state.runner.session_service.get_session(
        app_name=app.state.agent_app_name, user_id=_USER_ID, session_id=req.session_id
    )
    delta = record_followup_batch(session.state, req.answers)
    delta["language"] = req.language

    async def gen():
        async for chunk in _stream_turn(
            req.session_id, "I've answered the follow-up questions.", state_delta=delta
        ):
            if chunk["type"] == "final":
                chunk["session_id"] = req.session_id
            yield _sse(chunk)

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/api/translate-report")
async def translate_report(req: TranslateReportRequest) -> dict:
    """One-shot literal translation of an already-generated report into a
    different language, for the report screen's language switcher. The
    report was written once by InterpreterAgent in whichever language was
    selected at generation time — this translates the existing text rather
    than regenerating it, so switching back and forth doesn't produce a
    different narrative each time.

    Grounding concept labels are NOT translated here — they come straight
    from the curated MCP corpus, which already has a native-language label
    for each concept (concept_source / concept_source_zh); the frontend maps
    to that directly instead of running a curated label through a generic
    translator, which would drift from the actual curated phrasing.
    """
    sections = _SECTION_RE.findall(req.report)
    bodies = [body.strip() for _, body in sections] if sections else [req.report]

    translated_bodies = await _translate_items(bodies, req.target_language)

    if sections:
        names = _SECTION_NAMES.get(req.target_language, _SECTION_NAMES["en"])
        translated_report = "\n\n".join(
            f"## {names[i] if i < len(names) else sections[i][0]}\n{body}"
            for i, body in enumerate(translated_bodies)
        )
    else:
        translated_report = translated_bodies[0] if translated_bodies else req.report

    return {"report": translated_report}


# Static assets (e.g. img/thumbnail.png) referenced by frontend/index.html.
# Unlike /app, these are fine to let the browser cache normally.
app.mount("/img", StaticFiles(directory=os.path.join(AGENT_DIR, "img")), name="img")


@app.get("/app")
async def frontend_index() -> FileResponse:
    # This is under active development — no-store avoids the browser serving
    # a stale cached copy after edits (which is why "still showing
    # analyst_agent" was reported after the rename had already landed).
    return FileResponse(
        os.path.join(AGENT_DIR, "frontend", "index.html"),
        headers={"Cache-Control": "no-store"},
    )


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
