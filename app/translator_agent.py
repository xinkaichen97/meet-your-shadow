"""TranslatorAgent: one-shot literal translation for content that was
already generated in another language — the report body and MCP grounding
labels, when the user switches language after the report exists. This is a
UI-triggered action outside the Orchestrator's turn-based session, invoked
directly via its own throwaway Runner from the FastAPI layer (mirroring how
AgentTool spins up an isolated nested Runner internally).
"""

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

TRANSLATOR_INSTRUCTION = """
You are a literal translator. You will receive a numbered list of short text
items. Translate EACH item into {language_name}, preserving its exact
meaning and tone — this is translation, not a rewrite or summary.

Output ONLY the translated items, in the same numbered format, one item per
line, same count and order as the input, no extra commentary:
1. <translation>
2. <translation>
...
""".strip()


def create_translator_agent(language_name: str) -> Agent:
    """Factory for a fresh TranslatorAgent, targeting the given language."""
    return Agent(
        name="TranslatorAgent",
        model=Gemini(
            model="gemini-flash-lite-latest",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=TRANSLATOR_INSTRUCTION.format(language_name=language_name),
    )
