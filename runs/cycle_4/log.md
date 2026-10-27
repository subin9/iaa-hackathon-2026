# Cycle 4 — run log (operator: HS)

| Field | Value |
|---|---|
| Harness tag | harness-v4 (commit b901e9d) |
| Model / effort | claude-fable-5-1, effort xhigh, showThinkingSummaries on (user settings.json); Claude Code v2.1.229, API usage billing |
| Run location | `C:\Users\Guest1337\harness_run_c4` — fresh folder name (new Claude Code project dir: no auto-memory, no prior sessions), copy of `harness/` outside the repo, `memory/` removed before kickoff |
| Parent CLAUDE.md / user CLAUDE.md present? | none (`%USERPROFILE%\.claude\CLAUDE.md` absent; no CLAUDE.md in C:\, C:\Users\Guest1337, Documents, repo root) |
| Permission test (throwaway session) | not repeated (same isolated copy as cycle 1) |
| Start (SGT) | 2026-10-27 ≈17:08 (kickoff pasted verbatim; one-time folder-trust prompt only) |
| End (SGT) | 2026-10-27 18:07 — 59 min wall-clock; API 41m 53s |
| Interventions | none |
| Permission prompts seen | none after the folder-trust prompt |
| Cost / tokens (`/cost`) | **$22.29** — fable-5-1: 1.8k input, 184.3k output, 12.9m cache read, 491.8k cache write; haiku 1.4k/24; 40 requests, 96% from cache. Weekly Fable usage after the run: 64% |
| Code written | 2,011 lines added, 0 removed |
| validate_outputs result | PASS — 25 findings (23 rule-attributed, 2 novel); holdout 100% coverage; check_sub passes |
| Deliverables present | all required + stretch |
| Holdout grade (eval/grade_holdout.py) | D4_agent_baseline 0.1031 (motor 0.0710 / buildings 0.0306 / contents 0.0718) |
| Transcript | `runs/transcripts/353f1526….jsonl`, `runs/cycle_4/transcript.txt`, `memory_after_cycle4/`. Audit: **clean** — no reference outside the run folder, no web tools, no questions; auto-memory only **written** at the end (tool #188 of 192, a workspace status note), never read. |
| Anything odd | New repair found: sibling reconstruction of time-invariant policy attributes (F-18, verified exactly) — the first cycle to change the cleaned tables beyond cycle 1. |
