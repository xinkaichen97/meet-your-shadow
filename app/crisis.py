"""Crisis-keyword detection. Plain Python, never routed through the LLM. See
shadow_test_agent_spec.md section 9 — if is_crisis_text() is true, the caller
must respond with CRISIS_RESPONSE directly and must not invoke the Runner.
"""

CRISIS_KEYWORDS = [
    "kill myself", "want to die", "wanna die", "end my life", "end it all",
    "not worth living", "can't go on", "hurt myself", "self harm",
    "suicidal", "suicide", "no point anymore", "better off dead",
]

CRISIS_RESPONSE = """It sounds like things are really hard right now. This tool isn't equipped to
help with that directly, but you don't have to carry it alone.

In the US, you can call, text, or chat with the 988 Suicide & Crisis Lifeline
anytime, day or night — it's free and confidential. You can also text HOME to
741741 to reach the Crisis Text Line. If you're outside the US, please look
up your local crisis line, or reach out to someone you trust."""


def is_crisis_text(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in CRISIS_KEYWORDS)
