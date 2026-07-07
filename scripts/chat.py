"""Interactive local test harness for the Shadow Self-Reflection Agent.

Seeds session state via record_answers() (standing in for the FastAPI layer
that will do this in production), then drops into a REPL so you can chat
with the Orchestrator directly.

Usage:
    uv run python scripts/chat.py                    # answer all 16 questions yourself
    uv run python scripts/chat.py --answers a.json    # load answers from a file
    uv run python scripts/chat.py --sample            # built-in canned sample

answers.json format: {"q1": 3, "q2": 5, ..., "q16": 2}  (all 16 required, 1-5)
"""

import argparse
import asyncio
import json

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from app.shadow_data import QUESTIONS
from app.tools import record_answers

SAMPLE_ANSWERS = {f"q{i}": 3 for i in range(1, 17)}
SAMPLE_ANSWERS["q1"] = 1
SAMPLE_ANSWERS["q2"] = 5


def prompt_for_answers() -> dict:
    print("Scale: 1 = Strongly disagree, 2 = Disagree, 3 = Neutral, 4 = Agree, 5 = Strongly agree\n")
    answers = {}
    for qid, q in QUESTIONS.items():
        while True:
            raw = input(f"{q['text']}\n> ").strip()
            if raw in {"1", "2", "3", "4", "5"}:
                answers[qid] = int(raw)
                break
            print("Please enter a number from 1 to 5.")
        print()
    return answers


async def main(answers: dict) -> None:
    session_service = InMemorySessionService()
    initial_state = record_answers(dict(answers), {})
    session = await session_service.create_session(
        app_name="app", user_id="local", session_id="local-session", state=initial_state
    )
    runner = Runner(agent=root_agent, app_name="app", session_service=session_service)

    print("Seeded answers, starting conversation. Type a message and press enter.")
    print("(Ctrl+D to quit)\n")

    first_turn = True
    while True:
        try:
            if first_turn:
                user_text = "Here are my answers."
                print(f"> {user_text}")
                first_turn = False
            else:
                user_text = input("> ")
        except EOFError:
            break

        content = types.Content(role="user", parts=[types.Part.from_text(text=user_text)])
        async for event in runner.run_async(
            user_id="local", session_id=session.id, new_message=content
        ):
            for fc in event.get_function_calls() or []:
                print(f"  [tool call] {fc.name}({fc.args})")
            for fr in event.get_function_responses() or []:
                print(f"  [tool response] {fr.name} -> {fr.response}")
            if event.is_final_response() and event.content and event.content.parts:
                text_out = "".join(p.text or "" for p in event.content.parts)
                print(f"\n{text_out}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--answers", type=str, default=None, help="Path to a JSON file with q1..q16 answers")
    parser.add_argument("--sample", action="store_true", help="Use the built-in canned sample instead of answering live")
    args = parser.parse_args()

    if args.answers:
        with open(args.answers) as f:
            answers = json.load(f)
    elif args.sample:
        answers = SAMPLE_ANSWERS
    else:
        answers = prompt_for_answers()

    asyncio.run(main(answers))
