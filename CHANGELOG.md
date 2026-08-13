# Changelog

## 2026-08-12 — Personalize follow-ups, diversify reports, fix language switching
- Orchestrator rewritten as a deterministic Python `BaseAgent` (was an `LlmAgent`) — routing between specialist agents was always a plain function of state, so it no longer spends a Gemini call deciding it. Cuts real latency (quiz submission ~10.6s → ~7s, each chat reply ~7.5s → ~4-7s in testing).
- Fixed a state-persistence bug this surfaced: mutating a session fetched via `get_session()` never actually reached canonical storage (ADK returns a detached copy). Follow-up submission and mid-chat language switches now go through `state_delta` on `run_async` instead.
- Follow-up questions are now generated per-user by `FollowUpAgent`, grounded in the person's actual answers, instead of picked from 8 fixed templates — wording no longer repeats, and no longer cites raw scores.
- A follow-up now only fires on a genuine denial/projection conflict; previously the top-ranked shadow type always got one even with no real conflict.
- Report sections now draw on a computed secondary shadow type and different concrete evidence per section, instead of restating the same tension four times.
- Language switch on the report screen now translates the report body itself (was chrome-only before); "Relevant ideas" labels are mapped to the MCP corpus's curated native-language field instead of being machine-translated.
- Wait-screen text updates to "Generating your report..." at the right moment, including mid-submission when no follow-up turns out to be needed.
- Landing page now previews all 8 shadow-type titles before the quiz starts.
- Fixed several stiff, over-literal Chinese concept labels in the MCP corpus.

## 2026-08-11 — Cut Cloud Run cost, remove agent-trace UI
- Cloud Run scale-to-zero: `--min-instances 0 --max-instances 3 --memory 1Gi` now documented as required flags on `agents-cli deploy` in the README. The previous defaults (`--min-instances 1`, `4Gi`) kept one instance always warm 24/7, the root cause of a ~$60+/month bill.
  - Also edited `deployment/terraform/single-project/service.tf` to match, then discovered `agents-cli deploy` for the `cloud_run` target runs `gcloud beta run deploy` directly and never reads that Terraform file (it's only used for the `gke` target) — so the actual fix is the deploy flags above, not the Terraform edit. Left the Terraform edit in place since it's still correct, just not load-bearing for this deploy path.
- Removed the agent-trace UI (live "Calling X Agent..." status text and pill badges) from the quiz, follow-up, report, and chat screens — loading states are now generic.

## 2026-07-31 — Add Chinese version and language switch
- Full Chinese (zh) translations for all 16 questions, 8 follow-up templates, and 8 shadow-type titles/anchors.
- Top-right EN / 中文 language switcher, safe to use mid-quiz or mid-conversation without losing progress or retranslating already-generated content.
- `language` threaded through session state and into every agent's instruction.
- Chinese crisis-keyword detection added — previously crisis checks were English-only, a real safety gap for Chinese-speaking users.
- Report section headers and MCP grounding concept labels localized.
