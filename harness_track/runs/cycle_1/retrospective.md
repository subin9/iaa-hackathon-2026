# Retrospective

## What went well

- The Part 1 data-readiness checks transferred as methods: every one of them was run on every table, and the ones that found nothing (duplicates, unit clusters in premiums and claim amounts, test-file exposure) are recorded as negative results rather than silently skipped.
- Two checks found defects no rule anticipated — a second exposure convention (360-day basis) next to the day-count rows, and sum-insured unit errors in the *test* files — and both got a per-row decision rule (date recomputation; premium-to-sum-insured ratio) rather than a tuned threshold, so the same code applies to train, test and reference tables.
- Reconciliation closed to the cent at every stage: exposure totals before and after repair, claim count and net incurred before and after exclusion, Σ y in the modelling tables against the cleaned claims table, and the model's training level against Σ y_capped (through the intercept in the init score).
- The leakage work found the cohort-stamp pattern early (campaign_code nullness ⇔ join year; customer_since_year ≡ period year − renewal_count), which would otherwise have produced a model that separates 2025 perfectly for the wrong reason.
- The completion curve handled the two-year truncation honestly: the shape is estimated from the market's own claims with a right-truncation-corrected estimator, the borrowed part is one number per line, and both variants are carried in the modelling tables.
- Pre-registering the round-count grid and feature groups before scoring made the single-fold decisions auditable, and the grid caught a real problem (Part 1's 600 rounds over-fit the small lines).

## What was difficult or slow

- Wide-table printing on a Windows console (encoding, truncated columns) cost the first half hour; compact per-column summaries written to files worked. Next time: start with the column profiler, never print whole frames.
- The exposure categorisation went through three passes because tiny rows (1-6 days) round to the same value under every convention; classifying by ratio clusters first and treating the remainder as rounding would have been faster.
- The buildings level comparison was rewritten twice because fire makes "excluding large claims" ambiguous (top 1%, >2% of year, cap at a fixed amount give different stories). A fixed per-claim cap applied to both markets is the only like-for-like basis and should be the default.
- The adversarial validation needed four passes (all → minus time stamps → minus leakage → minus mix) before the residual was interpretable; doing the single-feature AUCs first would have ordered the exclusions in one pass.
- The first baseline run had no intercept in the init score, so levels drifted with the round count; this was only visible because the level reconciliation was printed next to the scores. Check Σ prediction = Σ target on the training rows before reading any score.

## Rules I could not apply as written

| rule | why it did not fit | substitute | what was lost or left uncertain |
|---|---|---|---|
| R-0102 completion curve from the most mature years | two accident years; only January-2023 losses reach 24 months | right-truncation-corrected (reverse product-limit) curve from all 2023-24 claims up to 18 months, share beyond 18 months borrowed from the developed market | the tail (2% of motor cost) is an assumption; ±1-2% on the motor 2024 level |
| R-0103 trend from mature years | one mature year | borrowed developed 2021-2023 completed slopes, rounded; zero-trend file as the second candidate | the 2025 level carries ±4.5% from trend alone; the emerging one-step check cannot discriminate |
| R-0105 IBNER with out-of-sample evidence | no year whose reserves are independent of 2024's | compared open vs closed by peril, recorded 0 to +6% as uncertainty | motor level could be understated by up to 6% |
| R-0201 time-ordered folds (plural) | one fold exists (2023 → 2024) | primary fold plus a policy-grouped within-training check labelled weaker | adoption evidence is one fold deep |
| R-0202 every fold in the same direction beyond noise | one fold; developed folds not run as a direction check | > 3 seed-sd on the fold and not worse on the secondary | changes adopted (round counts) may not replicate; feature-group findings are indicative only |
| R-0203 noise floor of ±0.001 | floor measured on 600k-row folds | re-measured from three seeds per line (0.0006 / 0.0042 / 0.0020) | property effects below ~0.01 D² are unreadable on one fold |
| R-0204 public-leaderboard noise | no submissions made | none | n/a for this phase |
| R-0205 / R-0305 blend weights | no blend built | single seed-averaged family | variance reduction from blending not realised |
| R-0306 claim-count credibility | 76% of test rows have no history | dropped | a small gain on the renewal quarter of the book is unexplored |
| R-0307 segment corrections on every fold | one fold | segments pre-registered and reported; nothing applied | the contents new-business gap (A/E 1.7 on 64 claims) is unaddressed in the file |
| R-0403 / R-0407 peril and acquired-book comparisons | ~500 property claims a year, 77 / 102 new-business property claims | comparisons made and labelled thin or not credible where below ~300 claims | fire, flood, subsidence severities and property new-business relativities are not estimable here |
| R-0404 default stance (borrow shape, re-estimate level) | several Part 1 shape components rest on columns the market lacks (integer age, mileage, telematics, credit band, region) | shape refitted on the common column set; those relativities dropped | lower discrimination than Part 1 is expected and observed |

## Judgment calls I am least sure about

1. Excluding the 36 pre-inception claims rather than shifting their loss year. Alternatives: +1 year (places 28 inside cover), assign to the first row. Chose exclusion because nothing in the record supports a specific correction and the amount is 0.33% of incurred; the claims system can settle it.
2. Deciding ×1000 sum-insured rows by the premium-to-sum-insured ratio rather than a value threshold alone. The ratio rule is self-calibrating, but it assumes the premium was rated on the correct sum insured; if premiums were also wrong the rule would miss those rows (none were seen).
3. Borrowing the developed tail beyond 18 months although the emerging market reports faster. Conservative by construction; the no-tail variant is in the tables. A third year of emerging data settles it.
4. Trend values (+3 / +6 / +5%) from a market whose own 2024 flattened. Two candidate files exist; the choice is the team's.
5. Keeping new_business and renewal_count as features although they separate train from test almost perfectly. They are the mix the model must price; the alternative (dropping them) would price the acquired book at the renewal level, which the training data contradict in motor and contents.
6. Not applying a new-business uplift to contents despite consistent evidence (training +30%, fold A/E 1.7, persistence into 2024). R-0307 asks for every fold; there is one. The number is written down for the team.
7. Excluding gender from the baseline although it improves the motor fold by 3.8 seed-sd. A rating-rule decision, not a modelling one.
8. Choosing round counts on the single fold. Pre-registered and large effects, but still one fold; the grouped secondary agreed in both cases.
9. Trend inside the offset rather than as a post-hoc multiplier. Equivalent for a constant factor per year; it changes nothing except where the assumption is visible.

## Proposed additions to this workspace's practices

1. **Proportionality check for unit errors.** When two amount columns should be proportional (premium and sum insured, paid and incurred), tabulate their ratio per row: a unit error in one column shows as a ratio shifted by a power of ten while the value itself may look merely large. Decide per row on the ratio, not on a value threshold. Applies whenever a monetary column is profiled (R-0003). Prompted by sum-insured errors in the test files that a value threshold alone would have tied to a tuned cut-off.
2. **Classify exposure mismatches by ratio cluster before repairing.** Compute stored/derived exposure, cluster the ratio (365 = day counts, 365/360 = 360-day basis, (n−1)/n = exclusive end, ≈1 = rounding) and report each cluster; then repair every row from dates. Applies under R-0001. Prompted by a second convention hiding behind the first.
3. **Lag-plausibility test for unlinked claims.** For claims whose loss date falls outside every period of their policy, compare their report lags with the matched claims' lag distribution; lags beyond the matched 99.5th percentile mark a date defect, not a late report, and the claims are excluded with a query rather than re-dated. Applies under R-0004. Prompted by pre-inception claims whose lags were all a year longer than anything matched.
4. **Cohort-stamp detection.** Cross-tabulate every customer attribute's value *and* its nullness against join year; any attribute that is a deterministic function of join year is a time stamp. Confirm with a single-feature adversarial AUC. Applies under R-0006 before any multivariate adversarial run. Prompted by a marketing code that was null exactly for pre-launch customers.
5. **Truncation-corrected lag curve as the default for short histories.** With fewer than three accident years, estimate the report-lag curve with a reverse-time product-limit estimator (each step uses only claims old enough to observe it), anchor at the oldest well-populated age, and borrow only the share beyond the anchor from the reference market; carry both the spliced and the no-tail variant. Applies under R-0102. Prompted by the two-year history.
6. **Intercept in the init score of offset-boosted models.** Add log(Σ target / Σ exposure-basis) to the offset so trees learn relativities; check Σ prediction = Σ target on the training rows before reading any score. Applies under R-0301/R-0304. Prompted by levels that moved with the round count.
7. **Re-choose capacity when volume changes by an order of magnitude.** Pre-register a small grid of round counts (half, default, double) and adopt by a written rule before scoring. Applies under R-0301 in any new market. Prompted by Part 1's round count over-fitting the small lines.
8. **New-business pre-model check.** When the prediction year is new-business dominated, compute the new-business frequency excess inside training, age-standardised, and the persistence of first-year policies into their second year, before modelling; then compare the model's new-business relativity with it. Applies under R-0406/R-0407. Prompted by a model that priced contents new business flat against a +30% data signal.
9. **Like-for-like large-loss basis across markets.** Compare line levels between markets with every claim capped at the same fixed amount; "excluding the top x%" means different things in a 1,000-claim and a 160,000-claim market. Applies under R-0403. Prompted by three different buildings stories from three cut-offs.
10. **Reconciliation ladder.** Write the chain exposure (raw → cleaned), claims (raw → cleaned), Σ y (tables → claims), model level (Σ prediction → Σ target) as one table and refuse to proceed while any link is open. Applies under R-0012 and R-0208. Prompted by how quickly the ladder caught the intercept problem.
11. **Run guardrail printouts on cleaned and raw history.** `check_sub.py` without `--cleaned` shows a history deflated by day-count exposures; the difference between the two printouts is a one-line proof that the exposure repair mattered and belongs in the validation note.

## Open questions and team queries

- F-07: 36 claims with loss dates before policy inception and year-long report lags — excluded; should the claims system re-date them?
- F-18: ncb_years exceeds years_licensed on 16-22% of motor rows, mostly young drivers and more so in the acquired book — which field is authoritative?
- F-19: no comparison-site commission in `expenses` while 5% of policies use that channel — missing loading or wrong channel label?
- Trend: candidate A (+3 / +6 / +5% a year, borrowed) or candidate B (zero)? `submission.csv` is A; `submission_zero_trend.csv` is B.
- IBNER: apply any uplift for 2024 open-claim reserving (0 to +6% motor)? Not testable locally.
- Contents (and motor) new-business level: adopt a shrunk uplift for new business in contents (+15-20% on 76% of rows → level ≈ 103-106) given the one-fold evidence?
- Gender as a rating factor in this market (improves the motor fold; regulatory question).
- Buildings fire load: are 2023-2024 (70 fire claims, 45% of cost) representative? A reinsurance or market view would move the buildings level by ±15%.
- Developed-market folds as a direction check for the feature-group decisions (not run).
- 10% of developed motor policy rows reference customers absent from the developed customers table — a Part 1 data question outside this scope, noted for the Part 1 owners.
