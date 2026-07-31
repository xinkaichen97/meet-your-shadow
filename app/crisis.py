"""Crisis-keyword detection. Plain Python, never routed through the LLM. See
shadow_test_agent_spec.md section 9 — if is_crisis_text() is true, the caller
must respond with CRISIS_RESPONSE directly and must not invoke the Runner.
"""

CRISIS_KEYWORDS = [
    "kill myself", "want to die", "wanna die", "end my life", "end it all",
    "not worth living", "can't go on", "hurt myself", "self harm",
    "suicidal", "suicide", "no point anymore", "better off dead",
]

# Simplified Chinese equivalents. Checked in addition to CRISIS_KEYWORDS
# regardless of the user's selected UI language — detection must not depend
# on a language toggle, since a Chinese-speaking user could type crisis
# language in Chinese while the interface is still set to English (or
# vice versa).
CRISIS_KEYWORDS_ZH = [
    "不想活了", "想死", "活不下去了", "撑不下去了", "结束自己的生命",
    "结束一切", "自杀", "伤害自己", "自残", "活着没有意义", "还不如死了算了",
]

CRISIS_RESPONSE = """It sounds like things are really hard right now. This tool isn't equipped to
help with that directly, but you don't have to carry it alone.

In the US, you can call, text, or chat with the 988 Suicide & Crisis Lifeline
anytime, day or night — it's free and confidential. You can also text HOME to
741741 to reach the Crisis Text Line. If you're outside the US, please look
up your local crisis line, or reach out to someone you trust."""

CRISIS_RESPONSE_ZH = """听起来你现在真的很不容易。这个工具没办法直接帮你处理这些，但你不需要一个人扛着。

在美国，你可以随时拨打、发短信或在线联系 988 自杀与危机热线，全天候提供免费且保密的帮助；
也可以发短信 HOME 到 741741 联系 Crisis Text Line。如果你不在美国，请查找你所在地区的
危机热线，或联系你信任的人。"""


def is_crisis_text(text: str) -> bool:
    lowered = text.lower()
    if any(kw in lowered for kw in CRISIS_KEYWORDS):
        return True
    return any(kw in text for kw in CRISIS_KEYWORDS_ZH)


def get_crisis_response(language: str = "en") -> str:
    return CRISIS_RESPONSE_ZH if language == "zh" else CRISIS_RESPONSE
