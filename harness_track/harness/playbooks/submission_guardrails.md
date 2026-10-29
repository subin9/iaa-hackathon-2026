# Submission Guardrails

The agent never submits. These rules describe what a submission file must
satisfy and how the team controls the submission process; the agent applies
the file checks and the humans apply the rest.

<!-- rule: R-0501 -->
- **File checks before anyone looks at a score.** Run
  `python tools/check_sub.py <file>`: row count equals the sample
  submission, `row_id`s unique and identical to the sample, no nulls, all
  predictions ≥ 0, and the predicted cost per exposure-year by line printed
  against the training-year history with the maximum prediction. Read the
  printout; a passing file with an implausible level is not ready.

<!-- rule: R-0507 -->
- **Print the level check on raw and cleaned history.** Run the guardrail
  once against the as-delivered tables and once against the cleaned tables;
  the difference between the two printouts is a one-line proof of how much
  the data repairs (exposure above all) moved the history, and belongs in
  the validation note. *(cycle 1, agent)*

<!-- rule: R-0505 -->
- **Prepare two candidates across the main level hypothesis; only one can
  be selected.** When the predicted level rests on an assumption that cannot
  be validated locally (completion tail, trend, acquired-book behaviour),
  prepare two candidate files that differ in that assumption, both
  validated. The competition allows exactly one Final Submission per team
  (Rules §2.2b; unselected = best public score is used), so the human
  chooses one and writes the reasoning down, including why the other was
  not chosen.

<!-- rule: R-0502 -->
- **Respect the stated submission limit and keep a team budget below it.**
  The Rules allow ten submissions per UTC day (§2.2a). The team plans its
  day's submissions in advance (probes, data-version checks, candidates)
  and never spends slots on differences the public score cannot resolve
  (R-0204).

<!-- rule: R-0503 -->
- **Every submission is logged**: UTC time, file name, commit hash of the
  code that produced it, local validation scores, public score, one-line
  description — in `submissions/log.csv` at the repository root.

<!-- rule: R-0504 -->
- **Nothing that is not ours leaves the workspace.** Data files (CC BY-NC),
  prediction files that include target columns, and credentials are never
  committed or shared. The repository guard (`tools/check_repo.py` at the
  repository root) enforces this on commit.

<!-- rule: R-0506 -->
- **Human sign-off.** A human reads the `check_sub` output and the
  reconciliation of predicted level to history (R-0208) before submitting,
  and records who submitted and why in the log.
