# Changelog

## 2026-08-12 — Personalize follow-ups, diversify reports, cut Cloud Run cost
- Orchestrator rewritten as a deterministic Python `BaseAgent` instead of an `LlmAgent` (routing was always state-based, not a judgment call), cutting real per-turn latency — this also surfaced and fixed a state-persistence bug where mutating a fetched session never actually saved.
- Follow-up questions are now generated per-user by `FollowUpAgent` from the person's actual answers (no more fixed templates or raw score citations), and only asked when there's a genuine denial/projection conflict.
- Report sections now draw on a computed secondary shadow type instead of repeating the same tension four times.
- Report language switch now translates the report body and maps "Relevant ideas" to the MCP corpus's curated native-language labels, instead of leaving both untranslated.
- Removed the agent-trace UI (live "Calling X Agent..." text, pill badges); wait-screen text now reflects what's actually happening.
- Landing page previews all 8 shadow-type titles; fixed several stiff Chinese concept labels.
- Cloud Run: documented `--min-instances 0 --max-instances 3 --memory 1Gi` on `agents-cli deploy` (previous defaults kept an instance warm 24/7 for ~$60+/month with no traffic).

## 2026-07-31 — Add Chinese version and language switch
- Full Chinese translations (questions, follow-ups, shadow-type titles) with a top-right EN/中文 switcher, safe to use mid-session.
- Chinese crisis-keyword detection added — previously English-only, a real safety gap.
- Report headers and MCP grounding labels localized.

## 2026-07-06 — Initial commit
- Scaffolded the ADK multi-agent app: Orchestrator + Analyst/Follow-Up/Interpreter/Companion agents, MCP Jungian-concept server, FastAPI + SSE backend, single-file frontend, Cloud Run deployment.
