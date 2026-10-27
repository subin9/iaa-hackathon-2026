# Cycle 3 — run log (operator: HS)

| Field | Value |
|---|---|
| Harness tag | harness-v3 (commit 366eb45) |
| Model / effort | claude-fable-5-1, effort xhigh, showThinkingSummaries on (user settings.json); Claude Code v2.1.229, API usage billing |
| Run location | `C:\Users\Guest1337\harness_run_c3` — fresh folder name (new Claude Code project dir: no auto-memory, no prior sessions), copy of `harness/` outside the repo, `memory/` removed before kickoff |
| Parent CLAUDE.md / user CLAUDE.md present? | none (`%USERPROFILE%\.claude\CLAUDE.md` absent; no CLAUDE.md in C:\, C:\Users\Guest1337, Documents, repo root) |
| Permission test (throwaway session) | not repeated (same isolated copy as cycle 1) |
| Start (SGT) | 2026-10-27 16:02 (kickoff pasted verbatim) |
| End (SGT) | 2026-10-27 16:46 — **44 min** wall-clock; API 40m 49s |
| Interventions | none (no prompts, no questions) |
| Permission prompts seen | none (bypassPermissions, read block off) |
| Cost / tokens (`/cost`) | **$19.09** — fable-5-1: 774 input, 186.5k output, 7.0m cache read, 400.4k cache write; haiku 1.4k/23 ($0.0002); 27 requests, 95% from cache. Weekly Fable usage after the run: 60% |
| Code written | 2,274 lines added, 2 removed |
| validate_outputs result | PASS — 25 findings (23 rule-attributed, 2 novel); holdout 100% coverage; check_sub passes for both candidates |
| Deliverables present | all required + stretch (submission, submission_no_trend, holdout_2024, validation) |
| Holdout grade (eval/grade_holdout.py) | D3_agent_baseline 0.1065 (motor 0.0766 / buildings 0.0427 / contents 0.0582) |
| Transcript | to copy: `~/.claude/projects/C--Users-Guest1337-harness-run-c3/*.jsonl` + `memory/` → `runs/transcripts/`; `/export` → `runs/cycle_3/transcript.txt`. Audit: pending |
| Anything odd | Fresh folder → no auto-memory available; first tool call went straight to the data. Agent added `max_delta_step` after its first run lost level (R-0311 gate worked as a gate). |
