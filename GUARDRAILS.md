# Trust, validation and guardrails

## Validation
- Local validation is time-ordered (train ≤ Y−1 → predict Y). Random
  K-fold across policy-years is prohibited (same policy spans years).
- A change is adopted only when every available fold moves in the same
  direction by more than the noise floor; single-seed results are never
  decisive (3-seed averages).
- When a validation rule cannot be applied as written (e.g. one fold only
  in the emerging market), the agent must say so, propose the closest
  substitute, and escalate it in the retrospective.

## Automated checks
- `harness/tools/validate_outputs.py` — all deliverables present, findings
  conform to `harness/schemas/findings.schema.json`.
- `harness/tools/check_sub.py` — row coverage, uniqueness, non-negativity,
  predicted rate per exposure vs history by line, max prediction.
- `tools/check_repo.py` — blocks commits containing data files or tokens.

## Human review and escalation
- The agent never submits to Kaggle. A human reads `check_sub` output and
  submits; every submission is logged (`submissions/log.csv`) with the
  commit hash.
- The agent lists its weakest judgment calls in `retrospective.md`; human
  review starts there.
- Rules are promoted into the harness only by the actuary, with provenance
  recorded in `harness/memory/registry.yaml`. Rules teach method, never
  market-specific answers.

## Submission controls
- ≤ 5 submissions per UTC day, regardless of what the platform accepts.
- Two final candidates covering the main level hypothesis split.

## Data and secrets
- Data (CC BY-NC 4.0) is never committed or redistributed.
- Kaggle token is rotated at the end of the competition.
