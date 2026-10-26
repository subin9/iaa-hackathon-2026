# Cycle 1 — run log (operator: HS)

| Field | Value |
|---|---|
| Harness tag | harness-v1 (commit 868a22f) |
| Model / effort | claude-fable-5-1, effort xhigh, showThinkingSummaries on (user settings.json); Claude Code v2.1.229, API usage billing |
| Run location | `C:\Users\Guest1337\harness_run` — copy of `harness/` outside the repo (no git context, no `../eval` reachable), `memory/` removed before kickoff |
| Parent CLAUDE.md / user CLAUDE.md present? | none (`%USERPROFILE%\.claude\CLAUDE.md` absent; no CLAUDE.md in C:\, C:\Users\Guest1337, Documents, repo root) |
| Permission test (throwaway session) | deny rules loaded; "Read ../eval/answer_key.md" refused by the agent citing CLAUDE.md (judgment, not a hard block) → run moved to an isolated copy |
| Start (SGT) | 2026-10-25 ≈23:15 (kickoff pasted verbatim) |
| End (SGT) | 2026-10-26 ≈01:05 — about 1h50 wall-clock; API time 45m 14s |
| Interventions | 2026-10-26 00:00 — repeated permission prompts (Bash) → switched session to auto mode (Shift+Tab). No content instruction given. No questions asked by the agent. |
| Permission prompts seen | Bash commands before the mode switch (allow rule `"Bash"` in project settings not honoured by this build); none after |
| Cost / tokens (`/cost`) | **$20.93** — fable-5-1: 4.0k input, 191.8k output, 13.1m cache read, 401.8k cache write; haiku-5-5: 1.4k input, 22 output ($0.0002); 50 requests, 97% of input from cache |
| Code written | 2,062 lines added, 3 removed (`work/p00…p40`) |
| validate_outputs result | PASS — 23 findings (15 rule-attributed, 8 novel); holdout 59,202 rows, 100% coverage; check_sub passes for both candidate files |
| Deliverables present | profile, findings.json, cleaned/ (13 tables + dq_flag_ columns), schema_mapping, shift_report, modelling_tables/ (3 + README), target_notes, adaptation_decisions, baseline/{submission, submission_zero_trend, holdout_2024, validation}, retrospective |
| Holdout grade (eval/grade_holdout.py) | D1_agent_baseline d2_all 0.1125 (motor 0.0754 / buildings 0.0760 / contents 0.0416); floor naive_2023_rate 0.0701 |
| Transcript | `runs/cycle_1/transcript.txt` via `/export` and the session JSONL copied from `%USERPROFILE%\.claude\projects\C--Users-Guest1337-harness-run\` (both gitignored). Audit for outside-folder access: … |
| Anything odd | Session was left open ~24h after completion and auto-compacted while idle (no effect on outputs). Weekly Fable usage after the run: 43%. |
