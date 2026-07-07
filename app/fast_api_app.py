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
from google.cloud import logging as google_cloud_logging
from google.genai import types
from pydantic import BaseModel

from app.app_utils import services
from app.app_utils.a2a import attach_a2a_routes
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback
from app.crisis import CRISIS_RESPONSE, is_crisis_text
from app.shadow_data import ANCHORS
from app.tools import record_answers, record_followup_batch

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


class MessageRequest(BaseModel):
    session_id: str
    text: str


class FollowupBatchRequest(BaseModel):
    session_id: str
    answers: dict[str, str]


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj)}\n\n"


async def _stream_turn(session_id: str, text: str) -> AsyncGenerator[dict, None]:
    """Sends one message through the Orchestrator, yielding a dict per
    call/response event as they happen (for live pill-badge display), then a
    final dict with the reply and the session state fields the frontend
    needs to decide what to render next.
    """
    runner: Runner = app.state.runner
    content = types.Content(role="user", parts=[types.Part.from_text(text=text)])
    reply_parts: list[str] = []

    async for event in runner.run_async(
        user_id=_USER_ID, session_id=session_id, new_message=content
    ):
        for fc in event.get_function_calls() or []:
            yield {"type": "call", "name": fc.name}
        for fr in event.get_function_responses() or []:
            yield {"type": "response", "name": fr.name}
            # InterpreterAgent's AgentTool has skip_summarization=True, so its
            # response event IS the final response (see google.adk.events
            # .event.Event.is_final_response) — there's no follow-up text
            # event to read, the reply is this function response verbatim.
            if event.is_final_response() and isinstance(fr.response, dict):
                result = fr.response.get("result")
                if result:
                    reply_parts.append(str(result))
        if event.is_final_response() and event.content and event.content.parts:
            text = "".join(p.text or "" for p in event.content.parts)
            if text:
                reply_parts.append(text)

    session = await runner.session_service.get_session(
        app_name=app.state.agent_app_name, user_id=_USER_ID, session_id=session_id
    )
    state = session.state if session else {}
    top_type = state.get("top_type")
    yield {
        "type": "final",
        "reply": "\n".join(reply_parts),
        "top_type": top_type,
        "top_type_title": ANCHORS.get(top_type, {}).get("title") if top_type else None,
        "followup_queue": state.get("followup_queue", []),
        "current_followup": state.get("current_followup"),
        "report_generated": state.get("report_generated"),
        "final_report": state.get("final_report"),
        "grounding_concepts": state.get("grounding_concepts"),
    }


@app.post("/api/answers")
async def submit_answers(req: AnswersRequest) -> StreamingResponse:
    """Seeds a new session from a submitted 16-answer batch, then streams the
    Orchestrator's first turn (analyst -> acknowledge follow-ups, or report)."""
    session_id = str(uuid.uuid4())
    initial_state = record_answers(req.answers, {})
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

    async def gen():
        if is_crisis_text(req.text):
            yield _sse(
                {
                    "type": "final",
                    "session_id": req.session_id,
                    "reply": CRISIS_RESPONSE,
                    "crisis": True,
                }
            )
            return
        async for chunk in _stream_turn(req.session_id, req.text):
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
    record_followup_batch(req.answers, session.state)

    async def gen():
        async for chunk in _stream_turn(
            req.session_id, "I've answered the follow-up questions."
        ):
            if chunk["type"] == "final":
                chunk["session_id"] = req.session_id
            yield _sse(chunk)

    return StreamingResponse(gen(), media_type="text/event-stream")


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
