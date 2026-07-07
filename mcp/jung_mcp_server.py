"""
Minimal MCP server for the shadow-test project.
Exposes one tool: search_jung_concepts(topic, shadow_type) -> list of matching passages.

Run locally with:
    python jung_mcp_server.py

This uses the standard MCP Python SDK's FastMCP helper, which is the simplest
way to stand up a tool server that ADK's MCPToolset can connect to.
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

CORPUS_PATH = Path(__file__).parent / "jung_mcp_corpus.json"
CORPUS = json.loads(CORPUS_PATH.read_text())

mcp = FastMCP("jung-concepts")


@mcp.tool()
def search_jung_concepts(
    topic: str, shadow_type: str | None = None, max_results: int = 2
) -> list[dict]:
    """
    Search the curated Jungian concept corpus for passages relevant to a topic.

    Args:
        topic: free-text keywords to match against the corpus (e.g. "anger", "asking for help").
        shadow_type: optional filter, one of the 8 shadow_type ids (e.g. "suppressed_anger").
            If provided, only entries tagged with this type (plus general entries) are considered.
        max_results: maximum number of passages to return (default 2, keep this low —
            the Interpreter should paraphrase, not dump every match into the narrative).

    Returns:
        A list of {"content": str, "concept_source": str} dicts, most relevant first.
    """
    topic_lower = topic.lower()
    candidates = []

    for entry in CORPUS:
        if shadow_type and entry["shadow_type"] not in (shadow_type, None):
            continue
        score = sum(1 for kw in entry["keywords"] if kw in topic_lower or topic_lower in kw)
        # also give a small boost to entries matching the requested shadow_type exactly
        if shadow_type and entry["shadow_type"] == shadow_type:
            score += 1
        if score > 0:
            candidates.append((score, entry))

    candidates.sort(key=lambda pair: pair[0], reverse=True)

    if not candidates:
        # fallback: return the general entries so the tool never returns nothing
        general = [e for e in CORPUS if e["shadow_type"] is None][:max_results]
        return [{"content": e["content"], "concept_source": e["concept_source"]} for e in general]

    return [
        {"content": e["content"], "concept_source": e["concept_source"]}
        for _, e in candidates[:max_results]
    ]


if __name__ == "__main__":
    mcp.run()
