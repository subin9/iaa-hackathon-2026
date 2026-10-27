# Retrospective

## What went well

- The data-readiness playbook transferred almost intact. Every Part 1 check (exposure recomputation, ratio-based unit
  test, content-key duplicates, loss-date linkage, lag plausibility, valuation check, large-loss listing, cohort-stamp
  cross-tabulation, adversarial validation, nulls-at-random test) ran as written and each either found the expected
  defect or returned a clean negative that is now on record. Classifying exposure mismatches by ratio cluster (R-0014)
  earned its place: a second convention was hiding behind the obvious one.
- The proportionality-ratio rule for unit errors was self-calibrating across four tables and both splits, and the
  log-ratio distribution showed an empty gap between the normal and error clusters, so the boundary decision was a
  one-line justification rather than a tuned number.
- Reconciliation held at every rung: cleaned rows, exposure, claim count, incurred, the sum of the target against the
  cleaned claims table, and (after a fix) the model total against the training total.
- The short-history completion method (R-0108) could be checked against the data itself: the oldest accident year
  observed at 12 and 24 months reproduced the ratio the spliced curve implies, which is the one empirical test a
  two-year market allows.
- Pre-registering the capacity grid with an edge rule turned the most consequential modelling decision (far fewer
  boosting rounds than Part 1) into a mechanical one.

## What was difficult or slow

- The model level. The Part 1 recipe puts the intercept in the init score and assumes the boosting preserves the
  total; on a small, regularised fit it did not, by 5–17% depending on the line, and the symptom first appeared as a
  mysterious under-prediction on the time fold. Next time: run the Σ prediction = Σ target check on the training rows
  **before** reading any fold score, and treat a failure as a bug in the pipeline, not as a property of the fold.
- Distinguishing mix from stamp. New-business and tenure columns separate training from test as strongly as genuine
  time stamps do, because the test year *is* new business. The single-feature AUC rule flags both; only the meaning
  test (same value, same meaning in both years) separates them. The playbook rule should say so.
- The 2023 survivor sample. Nothing in the tables announces it; it only shows when year-to-year persistence is
  measured and comes out at exactly 100%. It affects the primary validation fold and the level comparison between
  years, and I found it late.
- Windows console encoding and shell quoting cost several reruns; scripts now set UTF-8 explicitly and are written as
  files rather than inline.

## Rules I could not apply as written

| Rule | Why it does not fit | Substitute used | What is lost or left uncertain |
|---|---|---|---|
| R-0102 completion from the most mature accident years | No accident year is mature: the older of two is observed to at most 24 months, and the younger is the one that needs completing | R-0108: reverse-time product-limit estimate anchored at 12 months, tail borrowed from the developed market; no-tail and developed-only variants carried alongside | The share of cost reported after one year (material for motor) is an assumption; the older year's completion is entirely borrowed |
| R-0103 trend from mature years | Only one year is close to complete; a trend needs two | Borrowed range (flat to the developed-market slope) carried as two candidate submissions | The whole range is unresolved (several percent to over ten percent of the predicted level by line) |
| R-0201 time-ordered folds | Exactly one time fold exists | That fold as primary; a policy-grouped split within the training years as a labelled-weaker secondary | The secondary split leaks calendar effects and cannot test level drift; the primary trains on a survivor-only year |
| R-0202 adoption needs every fold in the same direction beyond noise | One time fold; the Part 1 noise floor was estimated on 20× more data | Primary gain above max(Part 1 floor, observed seed sd) and secondary gain positive; developed-market folds not used | Effects smaller than the seed spread (several thousandths of D² here) are undetectable; adoption rests mainly on one fold |
| R-0307 segment corrections when mis-predicted in the same direction on all folds | One fold, and the thin segments swing by tens of percent between the two years | Actual/expected tabulated and reported; no correction adopted | The new-business relativity of the property lines is unresolved |
| R-0306 policy-level credibility | Three-quarters of the test book has no history; the rest has at most two observed years | Not applied; history columns and years-observed carried in the modelling tables for a later test | Possible small gain on the renewal part of the book |
| R-0305 blend of diverse families | Volume too small to support several members with confidence, and time was spent on levels instead | Single seed-averaged family | Part 1's blend gain (a few thousandths) is forgone |
| R-0204 public-leaderboard noise | No submissions are made by the agent | Not applicable; noted for the human who submits | — |
| R-0412 reference tables must cover the portfolio | One channel's commission loading is missing | Left null and raised as a query; not filled | Premium build for that channel is blocked |
| R-0008 / R-0104 large losses | Fine as written, but the property lines have about a thousand claims, so the "top 1%" is ten rows | Applied as written, with the sensitivity stated | The redistribution multiplier is itself a thin-data estimate |

## Judgment calls I am least sure about

1. **Excluding, rather than re-dating or keeping, the claims whose loss date precedes every period of their policy.**
   Alternatives: keep them unlinked (no effect on targets, but the claims table no longer reconciles to the rows);
   attach them to the first period (invents a date). Chosen exclusion because the lag test marks them as date defects
   and their cost share is negligible. A code-book answer on how the acquired book's prior claims were loaded would settle it.
2. **Anchoring the completion curve at twelve months and borrowing everything beyond it.** A later anchor uses more
   emerging information but a much thinner risk set; an earlier one borrows more. The twelve-month empirical check
   supports the choice for motor; it cannot test the tail itself. Another year of data settles it.
3. **Keeping new-business and tenure as features despite their adversarial separability**, on the argument that they
   mean the same thing in both years. The alternative (dropping them) would price the acquired book at the renewal
   level, against a clear pre-model signal in two of three lines. The 2025 experience of the acquired book settles it.
4. **Enforcing the training total with one level factor per fit** instead of tuning the learner until it preserves
   the level on its own. It is transparent and reported, but it means the model's relativities and its level come
   from different mechanisms. A GLM member, which preserves the level by construction, would be the cross-check.
5. **Letting the pre-registered rule adopt the marketing and premium groups for motor** when Part 1 found marketing
   variables did not transfer and when "own premium" as a feature is circular for pricing. The rule was written before
   looking and both folds agreed, so I followed it; the team may prefer to override it on principle, and the lean-only
   result is in the validation file for that purpose.
6. **No new-business or segment correction for the property lines** despite large actual/expected swings, because the
   segments hold under a hundred claims. The alternative of shrinking toward the developed-market new-business
   relativity (a borrowed shape) is listed as an open decision rather than done.
7. **Normalising occupation to the base title and discarding the "self-employed" prefix** on the evidence that the
   prefix rate is uniform across titles including ones where it is meaningless. If a real self-employment flag exists
   somewhere, this throws it away.

## Proposed additions to this workspace's practices

1. **Level check is a gate, not a report.** Rule: after fitting any offset model, compute Σ prediction / Σ target on the
   training rows; if it differs from one by more than rounding, stop, and either fix the learner or apply and report
   an explicit level factor before any fold score is read. Applies to every boosted or regularised model with an
   offset. Prompted by a shallow, regularised Tweedie fit on a small market that lost a double-digit share of the
   level while its init score was correct.
2. **Meaning test before the stamp test.** Rule: a feature that separates training from test years is a time stamp
   only if its *meaning* changes with the calendar (join year, campaign existence, in-period counts); a feature whose
   values shift because the portfolio changed (new-business flag, tenure, age) is mix and must be kept, then
   evaluated on the shifted subset. Applies whenever the prediction year is dominated by a transferred or new book.
   Prompted by the new-business flag scoring like a stamp on single-feature AUC.
3. **Persistence audit of the first year.** Rule: for every training year, compute the share of policies that appear
   in the following year and the distribution of the end-of-period decision; a first year with complete persistence
   and no lapses is a survivor sample and must be labelled as such in the shift report and the validation design.
   Applies to any extract whose first year predates the extract's own history window. Prompted by a 100% persistence
   rate that no table announces.
4. **Ratio clusters before day counts.** Rule: when recomputing exposure, tabulate stored ÷ derived for *all* rows and
   name every cluster, including those within a few percent of one; a 360-day or exclusive-end convention sits inside
   the "looks fine" range and only shows as a spike in the ratio. Already partly in R-0014; the addition is that the
   check must be run on the residual after the obvious cluster is removed, and on the test files separately (they may
   come from a different system and be clean).
5. **Empty-gap boundary for unit errors.** Rule: after computing the log-ratio of two proportional amount columns,
   report the widest empty interval between the normal mass and the power-of-ten cluster and place the boundary inside
   it; if no empty interval exists, the ratio rule alone is insufficient and a second column must be brought in.
   Applies to every unit-scale repair. Prompted by a row sitting just inside a "100× below the median" boundary that a
   "10× below" boundary caught with the same certainty.
6. **Capacity grid with an edge rule.** Rule: when the training volume changes by an order of magnitude, pre-register a
   round-count grid *and* the action when the best point is at the grid edge (halve or double and re-test, down to a
   floor), so that extending the grid after seeing the result is part of the registered procedure. Prompted by the
   lower edge winning on every line.
7. **Empirical completion check from the oldest year.** Rule: whenever a lag curve is spliced or borrowed, compare the
   oldest accident year's cost reported by 12 months with its cost reported by the valuation date against the ratio the
   curve implies for those two ages, cost-weighted and capped. Applies to any market with at least two accident years.
   It is the only direct test of the completion level a short history allows.
8. **Open-claim selection effect.** Rule: when comparing open and closed average costs by peril (R-0105), state that
   open claims are a selected sample (large claims close late) and compare like with like (open claims of the older
   year at the same age, where available) before reading an implied uplift. Prompted by negative "uplifts" in two lines.
9. **Free-text noise test.** Rule: for a categorical column with more distinct values than the code list, normalise case
   and whitespace, then test whether any remaining prefix or suffix variant occurs at the same rate in every base
   category; a uniform rate marks a random corruption to strip, a non-uniform one a real attribute to keep as a flag.
   Prompted by a "self-employed" prefix attached at the same rate to retired and student records.
10. **Reference-table coverage as a findings item.** Rule: join the channel / product / segment lists of the policy
    tables to every loading table and record a finding for each missing or null entry with team_query set. Already in
    R-0412; the addition is that it belongs in findings.json so it is not lost between the data and premium phases.

## Open questions and team queries

Flagged `team_query` in findings.json: F-CLM-PREINCEPT (pre-inception claims: mis-keyed dates or acquired-book
history?), F-SURVIVOR-2023 (how the first training year was extracted), F-EXPENSE-MISSING (comparison-site
commission), F-WEATHER-2025 (are prediction-year weather values forecasts or realised, and may they be used),
F-NCB-GT-LICENCE (definition of no-claims years), F-GENDER (permissibility as a rating factor).

Open decisions in adaptation_decisions.md: trend candidate A or B for the final submission; whether to borrow
developed-market new-business and age relativities as a prior for the property lines; whether to override the
pre-registered adoption of marketing and own-premium features for motor; credibility and blend members as next steps;
confirmation of the construction-code pairing used in the schema mapping.

Unresolved for validation: no honest second time fold exists, so every adoption rests on one fold with a seed spread
several times Part 1's noise floor; the team's common out-of-time file (`holdout_2024.csv`) is produced from a
survivor-only training year and a complete test year, and its level gap should be read with that in mind.
