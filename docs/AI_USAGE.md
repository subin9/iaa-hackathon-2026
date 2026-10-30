# How AI was used, and how its output was checked

The team used two AI set-ups with different jobs. Both are described here so a reader can tell which output came from an agent, which
decisions a person made, and how each claim was checked.

## 1. Modelling track: a coding agent in the terminal

Tool: Claude Code (Anthropic), a terminal coding agent running Claude models, working in this repository on a local machine.

What the agent did:
- wrote and ran every script in `src/`, `eda/` and `part2/`: data preparation, exploration, models, experiments, probes, tests, figures,
  the report builder and the working logs;
- proposed directions to try, and reported negative results with their numbers (most experiments in `part2/LOG.md` and `docs/part1_log.md`
  were rejected);
- submitted files to Kaggle with the Kaggle CLI, using the team member's token passed per command, after the team member had set the
  submission budget for the round;
- wrote the first draft of the report and of the video script.

What a person decided:
- the goals of each round and the submission budget (for example "five submissions for this improvement round");
- which data to bring in (the teammate's cleaned files and feature list);
- the use of gender as a rating factor (allowed in the emerging market; flagged for sign-off before any tariff uses it);
- the final submission, selected in the Kaggle interface.

How the output was checked:
- **Numbers are copied, not written.** Every number in the logs and the report comes from script output named next to it. The report builder
  reads its numbers from `work/p2/report_numbers.json`, `part2/probes.json`, `part2/final.json` and the office premium table.
- **Tests from failures.** `part2/tests/test_part2.py` holds 22 tests, most written after something went wrong: LightGBM reading columns by
  position (D2 0.036 instead of 0.134), a double level correction (+12% on motor), a feature leak into the emerging-only model, a recode that
  turned 90% of construction types into missing values. The correction stage is tested against a planted effect and against 20 null runs.
- **Independent review.** A fresh agent, given the code but not our conclusions, reviewed the probe solvers. It found that the Tweedie
  deviance constant was missing (it biased the solved factors away from 1) and that two tests could not fail. Both were fixed; the fixed tests
  were mutation-checked (a deliberately broken adapter now fails them).
- **Paired comparisons.** Model changes were compared on the same folds with a paired bootstrap by customer (2,000 resamples), not by two
  separate CV scores, which differ by up to 0.003 for the same model on different fold assignments.
- **Rules before results.** For every late submission the keep-or-drop threshold was written into `part2/LOG.md` before the public score came
  back, and the rule decided. Three CV-validated changes (v9, v10, v11) were measured this way on the public rows; two lost, and the log
  records the lesson that cross-validation on 2023-24 does not predict the 2025 broker book at that margin. The fourth, a fire slope carried
  from the developed market (v12c), won on both, and the segment factors measured on the board afterwards (v13, v14) were kept by the same kind of rule.
- **Disclosure.** Every leaderboard probe is listed with its score in `part2/probes.json` and in the report.

## 2. Data track: a rule-driven data harness (teammate)

The teammate wrote a rule book of method from the Part 1 experience (50 rules of method, not answers) and had an agent audit the emerging
files against it. Each cycle's new findings were turned into rules (50, 63, 67, 68 rules after cycles 1 to 4) until a cycle found nothing
new. The harness does not see evaluation data and does not submit; the actuary reviews every finding. Its output, the cleaned emerging
files, was used for the final Part 2 submission. The harness itself and its scorecards are maintained by the teammate.

What the modelling track checked about the cleaned files (`part2/e21_cleaned_data.py`): the change that reaches the model tables is the
missing vehicle and property fields filled from the same policy's other rows (90 to 100% agreement where both exist); the 36 claims it
removes fall outside every policy period, so the target is unchanged. Effect in paired CV: +0.00009 (sd 0.00019) for the files alone,
+0.00098 (sd 0.00034) with the teammate's feature list.

## 3. Other AI use

The video uses AI-generated narration and motion graphics (made by the teammate); the end card says so.
