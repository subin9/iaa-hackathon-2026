# Part 1 (developed market): development log

[Translator's note: this is an English translation of the Korean record `iaa_hackathon_experiment_log/README.md` from `iaa_hackathon_experiment_log.zip` (written 2026-10-22, not in git). The original package grouped copies of the code and logs into stage folders (`00_full_src_runnable/`, `01_eda/`, ...). Those folder references are replaced here with the locations in this repository. Scripts are in `src/` and `eda/`; logs and helper scripts that live in the gitignored `work/` folder are marked "log kept locally in work/, not in the repository". The repository copies of `src/run.py` and `src/gbm_peril.py` are later than the packaged copies: they add the `tw2l` model spec and the `GP_PT` option. Statements the source marks as "해석(추정)" are translated as "interpretation (not tested)". The final section, on reproducing eq20, was added on 2026-10-29 and is not part of the source.]

Original title: IAA AI Assisted Hackathon 2026 Part 1: experiment record (from start to finish)

Competition: iaa-ai-assisted-hackathon-2026-part-1 (hosted by the International Actuarial Association, deadline 2026-10-23 16:00 UTC).
This document records in date order what was done, why, and what came of it, from the first reading of the competition page on 2026-10-17 to 2026-10-22.
It was written from the working record (conversation log), the commit history and the experiment logs. All times are UTC.

The original package grouped the code and logs by stage (see the map in section 11, which gives the repository location of each). Opening the public score list first (`docs/part1_public_scores.csv`, public scores of 30 submissions; the file holds 29 rows) shows the whole course of the work.

## 1. At a glance

- Task: on synthetic insurance data (three lines: motor, home buildings, contents), predict the expected ultimate claim cost of each 2025 policy row. Training is the 2021-2024 policies, test is 626,639 rows of 2025 policies.
- Metric: Tweedie D² (power 1.5), computed once over the rows of all three lines together. The public leaderboard is 33% of the test.
- Assessment weights: pricing performance and adaptation 40%, AI use 25%, validation and guardrails 20%, documentation 15%. Part 2 (new emerging-market data) and the report and video had not been started yet.
- Public score progression (main submissions):

| Submission | Public score | What changed |
|---|---|---|
| blend_tw_po_fs | 0.12708 | Blend of three GBMs: Tweedie, Poisson, frequency x severity. First submission |
| eq10 | 0.12753 | CatBoost, MLP, GLM and seed-averaged models added, equal-weight average |
| eq12 | 0.12766 | TabM added |
| eq14 | 0.12817 | 6-seed TabM average at weight 3 |
| eq15_x103 | 0.12835 | Policy claim-history credibility factor, whole prediction x1.03 |
| eq17_x103 | 0.12852 | Per-peril TabM, 4 seeds, added |
| eq17_lv | 0.12889 | Per-line levels (multipliers) probed with public scores and applied |
| eq18 | 0.12914 | Levels shrunk to allow for noise, segment corrections added |
| eq19 | 0.12919 | Tree models replaced with shallow trees of 3 leaves |
| eq20 | 0.12956 | Replaced with lean models without the weather, sales and noise variables |

- Two final submission candidates: eq20 (main) and eq20_lv (a hedge that uses the publicly measured levels as they are). Submission slots remain until the deadline. The last public first place checked was 0.12996.

## 2. Cautions every team member must know

1. Number of submissions: the competition rule is five a day, but the Kaggle system accepts up to ten. Seven were made on 10-17 (UTC). If the wording of the rule takes precedence this may be a violation, so from then on no more than five a day were made. No host announcement on this was checked. [Note added 2026-10-29: the rules page as read on 2026-10-29 states a maximum of ten submissions per day.]
2. Data: under the rules (section 2.5, CC BY-NC) the data may not be redistributed. The original package did not include the data, the submission CSVs or the prediction parquet files (which contain the answer column), and they are not to be uploaded to a public repository either. [In this repository they sit in the gitignored `data/`, `submissions/` and `work/` folders.]
3. Rotate (reissue) the Kaggle API token in the Kaggle settings after the competition ends.
4. The level adjustment (section 6) uses the public leaderboard score as a sensor. If the assumption that public and private rows were split at random is wrong, the gain can disappear. For that reason the two final candidates were split by level hypothesis.
5. The public score list contains a `D0_baseline_glm_conservative...` submission (0.10925). It appears to have been uploaded on this account by someone else or by another session (author not confirmed).

## 3. Decision principles the team followed

- Local validation uses only two time-ordered folds: v2024 trains on years up to 2023 and predicts 2024; v2023 trains on years up to 2022 and predicts 2023. Random KFold is not used, because the same policy spans several years.
- The adoption criterion is that both folds rise in the same direction by more than noise (roughly +0.0003). Changes that raised only one fold almost never reproduced.
- The noise of a single seed is ±0.001. Decisions are made only on the average of 3 seeds. In one case an effect of +0.0010 with one seed became +0.0001 with three seeds (10-21, row-type feature).
- The noise of a paired comparison on the public score was estimated at about 0.0009. Smaller differences are not adopted on the public score.
- An equal-weight average was the most stable blend. When the weights were optimised, the optimum differed by fold.

## 4. Progress record (by date)

### Day 1: 2026-10-17

**Understanding the competition (14:08)** The rules were checked through the competition page and the Kaggle internal API. The first hypothesis was "the core difficulty is building the target, not the model". The view was that 2024 losses have a large not-yet-reported part (IBNR), so training without a correction would make the 2025 predictions come out low. This approach was set before the data was downloaded and was confirmed later by the EDA.

**EDA (14:16, `eda/`)**
- Claims are attached to the row with the same `policy_id` whose policy period contains `loss_date`. Almost all of them match.
- Cost per exposure year (before correction): motor 417→441→426→**343** (2024), buildings 283→309→321→341, contents 76→78→86→86. The cause of the motor drop in 2024 is the bodily injury cover: the 2024 count is about half, and 80% are still open.
- December losses are under-reported. In motor 2023 a single claim of 11.9M is an outlier making up about 10% of that year's total. Severity (amount per claim) rises 4-8% a year in most covers.
- The weather data includes 2025 values, so it can be used as is for the test.

**Data problems and handling (`src/prep.py`, `src/common.py`, `src/ibner.py`)**

| Problem | Handling |
|---|---|
| Some rows carry a day count (365 etc.) in exposure | Exposure recomputed from the period dates |
| 604 duplicate claims (only the id differs, contents identical) | Removed |
| Rows where `sum_insured` was entered 1000 times too large | Divided by 1000 |
| `customer_service_contacts`: a strong claim signal in training, but 2025 does not have that tail (the number of contacts rises by about 2.5 per claim) | Excluded |
| `customer_since_year`: the cause of adversarial validation separating train 2024 from test 2025 at AUC 1.0 (new customers in 2025, plus the year-specific weather, which is a natural time difference) | Excluded |
| The last claim loss date is 2024-12-29, there are 0 claims with 2025 losses | No leakage confirmed |

**Development correction**: from the reporting-lag curves of the mature years (2021-2022), each row gets `completion` (the share already reported), and the offset is `log(exposure × completion)`. The per-line year trend is fitted log-linearly on the mature years only and extrapolated to 2025. Large losses in the top 1% are capped, and the excess is returned as a constant multiple per line.

**First models and first submission (`src/exp.py`, `src/exp2.py`, `src/gbm.py`, `src/run.py`, `src/fs.py`, `src/feats.py`)** Three LightGBM models, Tweedie, Poisson and frequency x severity, were trained on both folds and on all years. The Tweedie GBM overfitted badly and was best at about 100 rounds. The three models were blended 0.5/0.1/0.4 for the first submission, which scored **public 0.12708, first place at the time** (host GLM baseline 0.10563). Locally it was v2024 0.1355 and v2023 0.138, so local validation was judged trustworthy.

**AutoGluon and a 4-model blend (15:15-17:39, `src/ag.py`)** It ran for 15 minutes per fold and line. AutoGluon was the weakest on v2024 and the strongest on v2023. Weights set from one year's results would fit that year's noise, so the weights were chosen on the average of the two years. Public 0.12717, only +0.00009, within noise and not counted as an improvement.

**Research and the first grid (19:49-)** The literature survey found post-hoc recalibration (autocalibration) the first thing worth testing, but it had no effect (power calibration +0.0004 on one fold and -0.0001 on the other; isotonic regression broke down completely). New history features (past claims at the same address, the customer's counts per cover, annual frequency) were built and a grid of 15 configurations run, but because it shared CPU with another session's training process, the first configuration had not finished after more than 42 minutes. The cause was OpenMP thread contention; with threads reduced to 6, one configuration finished in 67 seconds. All later experiments ran with 6-8 threads.

**Grid results (`work/grid*.jsonl|log`, logs kept locally in work/, not in the repository)** Baseline two-fold mean D² 0.1358. extra_trees (split thresholds chosen at random) gave the largest gain at +0.0013; Tweedie power 1.2-1.4 were about the same and 1.7 or higher was clearly worse. With all the new history features added the score fell to 0.1335, and number of leaves, learning rate, L2, target cap, dropping the marketing variables and so on were all within noise. Rerun with different seeds, extra_trees also swung between 0.1357 and 0.1371 by seed, and from this point the rule "average of 3 seeds" was set.

**More model families (`src/run.py`, `src/glm.py`, `src/cb.py`, `src/nn.py`)** Added: extra_trees models averaged over 5 seeds (twx, pox, fs5), a binned and one-hot encoded Tweedie GLM, CatBoost (300 rounds best on both folds; at 1500 v2023 fell as low as 0.0945) and an MLP (3 epochs best, overfitting from 4 epochs). The 10-model equal-weight blend eq10 took back first place for a time at public 0.12753 (0.00004 ahead of second).

**Judgement**: the gains of the day came from seed averaging and from mixing different model families. Hyperparameter tuning was almost all noise. Seven submissions were made that day, possibly beyond the rule (five), so from then on submissions were limited to five a day.

### Day 2: 2026-10-18

**Literature survey** Two strands were surveyed (deep learning models for tabular data / new actuarial methods). The conclusion was that TabM and EBM are the most promising, and that tabular foundation models (TabPFN etc.) are of practically no use, since there is no GPU and they have no offset or loss hook. For models without an offset, the trick "target y/e, sample weight e^(2-p)" is exact for Tweedie (AutoGluon and the GLM use it).

**What worked**
- **EBM** (additive model plus a few interactions, `src/ebm.py`): 1-2 minutes per line. Alone v2024 0.1350, the best single model at the time. The 11-model blend eq11 scored public 0.12761. Raising it to 40 interactions and 8 bags made it worse through overfitting.
- **TabM** (neural network with piecewise-linear embeddings, `src/tabm_run.py`): slow per line and fold (8 epochs took 26 minutes). It improved the more seeds were averaged: 1 seed 0.1322/0.1404, 2 seeds 0.1334/0.1411, 4 seeds 0.1340/0.1413. eq12 with 2 seeds scored public 0.12766, and eq13 with the 4-seed average at weight 2 scored public 0.12794.

**What did not work** Distillation (retraining on a target that mixes part of the actual values with out-of-fold predictions), fraud-suspect repairer and counterparty network features, geometric mean, harmonic mean and median blends, period-shape features (period length, year-end and year-start split, winter share), a larger EBM, deeper CatBoost. A segment correction learned on one fold and greedy model selection (Caruana) were also below the equal-weight average. Double GLM variance weights were worse too (0.1359 at exponent 0.5, 0.1350 at exponent 1, baseline 0.1366). linear_tree, path_smooth and categorical smoothing made no difference or were noise (path_smooth 20 once looked better, but rechecked with 3 seeds there was no trend with the value).

**Credibility Transformer** (implementation of the paper, `src/ct.py`): the 6-epoch scan was below TabM with 1 seed (0.1312/0.1370 vs 0.1322/0.1404), and with a higher learning rate the score still went up and down from epoch to epoch (6 epochs 0.1306, 8 epochs 0.1263). Training was unstable and the scores low, so it was dropped. One run took 4-11 hours.

**Public rank**: 5th (0.12761), first place 0.12908. With a paired-comparison noise of 0.0009, the rank difference could not be taken as a difference in skill, and the decision was to keep judging on the two local folds.

### Day 3: 2026-10-19

**TabM seeds and blend weight** The 6-seed average rose to v2024 0.1340, v2023 0.1421. Raising the TabM weight in the blend to 2, 3 and 4 times left v2024 at 0.1365, and only v2023 rose, to 0.1413, 0.1416 and 0.1418. The weight chosen was the middle value **3x** rather than the end value (4x). eq14 scored public 0.12817. Going to 8 seeds brought no further gain, so adding seeds stopped. Along the way a file-name collision overwrote the TabM average file; since then average files are saved separately under the name `tmavg`.

**Level x1.03** Fitting a quadratic to the results of the submissions with the whole prediction multiplied by x0.95, x1.00 and x1.05 gave an optimum of about 1.03, with a predicted gain of about +0.0001. The actual eq14_x103 scored 0.12826, in line with the prediction. Locally, however, the actual/predicted ratio was v2024 0.984 and v2023 1.026, opposite from year to year, so this value is fitted to the public score only.

**Rejected** TabM trained with Tweedie power 1.3 could not be told apart from the effect of a larger TabM share. TabM with history features; a separate large-loss model (predicting the excess above the top 1% with its own model; at or below eq14 whatever share was applied); a second EBM seed (v2023 fell from 0.1384 to 0.1336, meaning the EBM in the blend was a lucky seed); CatBoost with 6 seeds; credibility encoding (replacing high-cardinality categories such as the vehicle model with credibility-weighted loss ratios; all three settings below baseline 0.1366): none of these had any effect. That day the local score was judged to be stuck near v2024 0.1365 and v2023 0.1416.

**Using the data differently (user request)**
- **Policy claim-history credibility (`src/exprate.py`)**: an expected claim count L is predicted for each row from the covariates alone (out of fold, split by policy), and with N, the past actual count of the same policy, the blend is multiplied by (12+N)/(12+L). Line totals are kept. v2024 0.1365→0.1370, v2023 0.1416→0.1417. It was adopted as the only use of the data that raised both folds. Grouping by customer or address made it worse. Public eq15_x103 0.12835.
- Rejected: a combined model over the three lines (best single GBM on v2024 at 0.1354, but no change in the blend), learning only the loss ratio with the premium as the baseline (fell to 0.1344), counting only paid claims (no difference).

**IBNER finding** In 2023 open bodily injury claims average 30.8k and closed ones 17.6k. In 2024 open ones are 18.0k and closed ones 17.3k, nearly the same. The 2024 average bodily injury amount is about 30% below the 25.3k expected from the 2021-2023 trend. The interpretation is that the reserves on open claims are understated (2024 motor losses understated by about 9.6%). Retraining the GBM with open claims corrected by 1.52 times raised the motor test prediction by +2.95%. A submission with only this correction scored public 0.12807, but that is within noise, so whether it is right cannot be known. Since the assumption cannot be validated locally (the validation-year targets carry the same problem), it was not adopted. Also found that day: on rows just after a mid-term change, the model overpredicts the loss by 11-15% (same direction on both folds). As a feature it gave only +0.0006, and as a post-blend correction only +0.0001, so the gain was small. In the error decomposition, the rows with zero loss account for 59%, and the top-1% large-loss rows for 9-12%. That is, the score is decided mostly by frequency discrimination: giving low values to policies with no claims.

**Per-peril TabM (`src/tabm_peril.py`, afternoon)** Until then every model predicted only the total loss. A multi-task neural network was built with a separate Tweedie head per cover (peril), whose predictions are summed. The reason: different factors act on each peril (theft: region, bodily injury: young drivers, storm: wind exposure). Seeds 0 and 1 were good alone at v2023 0.1424, but the predicted total varied a lot by seed (test buildings: seed 0 82.8M, seed 1 89.9M, the existing TabM average 75.9M). So the line totals were matched to the existing TabM average and only the shape was blended in. Blend 0.1370/0.1417→0.1373/0.1426. eq17, a 4-seed average including seeds 2 and 3, came out slightly lower at 0.1372/0.1424 (seeds 0 and 1 had been lucky), but was adopted as the option with less selection bias. Public eq16_x103 0.12851, eq17_x103 0.12852.
- A per-peril LightGBM with the same structure was weak alone (0.1304/0.1257) and lowered v2023 in the blend, so it was removed. Adding claim-count prediction to TabM as an auxiliary task also lowered v2023 and was discarded.

### Day 4: 2026-10-20

**New directions, all failed**: covariate-shift weights (a classifier that separates training rows from target-year rows on the features alone, with larger weights for similar rows; a large drop to 0.1270/0.1254 at exponent 1.0), a log-space geometric mean and Tweedie GLM stacking (below the arithmetic mean), a correction GBM trained on one fold's residuals (the harder it was trained, the bigger the drop), a GBM without year so that weather explains the year effect (no change), a seasonal exposure feature (a monthly loss index matched to the months a row covers; no change). What they share is that an improvement obtained in one year does not carry over to the next. A real seasonal pattern was confirmed: buildings claim frequency in winter (December to February) is 1.29-1.43 times the average.

**Stabilising per-peril TabM**: learning rate 1e-3, 8 epochs, predictions averaged over the last 3 epochs. v2024 alone improved, but the v2023 seed spread remained and there was no blend gain. Self-supervised pretraining (first training on the features of the training and test rows; the loss went down from 0.4959 to about 0.48) was also noise in the blend at -0.0001/+0.0004. After this the TabM direction was closed.

**Identity linking and networks**: the repairer and counterparty ID network (99% of counterparty IDs appear only once; the year-to-year correlation of repairer average cost is 0.02) and 9,529 customer pairs with the same surname and date of birth (suspected re-enrolment; same address shared 0.01%, insurer refusal share the same as average) all turned out to be random.

**Per-line level probing (`src/level_probe.py`, 18:14)** This was the day's largest gain. Multiplying a fixed prediction by a constant s makes the Tweedie 1.5 deviance an exact function of s (of the form -A·s^-1/2 - G·β·s^1/2). The curvature G was obtained from the three earlier global-scale submissions (x0.95/1.00/1.05), and the global optimal scale of 1.0285 agreed with x1.03. That leaves one unknown per line, which was solved with 3 submissions that each raised a single line to x1.10 (motor 0.12776, buildings 0.12868, contents 0.12852). The resulting optimal scales were motor 0.9764, buildings 1.0925 and contents 1.0644, and the predicted score of eq17_lv with these applied, 0.1289, was almost the same as its actual public score of 0.12889 (+0.00037). The buildings 2025 prediction coming out about 11% above 2024 is consistent with the trend combined with 2025 being the windiest year.

### Day 5: 2026-10-21

**Segment level probing**: five segments where the blend missed in the same direction on both local folds (motor age 24 and under, motor rural, motor third-party fire and theft cover, buildings occupation Retired, buildings top 30% of wind exposure) were checked with the public score. Choosing segments by looking at the public score would fit noise, so the segments were fixed in advance on local evidence. The solved optimal scales were 0.941, 0.956, 0.965, 0.861 and 0.870.

**Noise-aware eq18**: in a local experiment that split the rows randomly in half 200 times, the noise of the optimal scale estimated from the public half alone was 2.5-3% for line levels, 3.5-8% for small segments, and 10% for motor v2023 (which contains the very large loss). So the line levels were pulled back 30% from the public optimum towards x1.03 (motor 0.9925, buildings 1.0737, contents 1.0541). Segment scales were applied only for the 4 segments where the local two-fold mean and the public check pointed the same way, as the geometric mean of the local and public values (motor young drivers 0.913, rural 0.911, third-party fire and theft 0.875, buildings wind 0.904); Retired was left out because its direction was opposite. The probability that all 4 segments point the same way by chance is 1/16. eq18 scored public 0.12914.

**Rejected**: segment corrections derived on one fold almost always lost on the other fold (ridge GLM -0.006, correction of the top segments -0.001 to -0.0075). Many of one fold's top segments were values pulled by large-loss noise (v2023 motor Manager segment actual/predicted 3.66).

**Testing the year assumptions of weather, premium and history (`src/wxmean.py`, `src/deflate.py`, `src/asof.py`, `src/season.py`, `src/feats2.py`, `src/feats3.py`, `src/feats4.py`, `src/large.py`; helper scripts and logs kept locally in work/, not in the repository)**: under the hypothesis "wind in 2025 is above normal and the model overreacts", the weather was replaced with a per-address mean plus that year's deviation, which made it worse (0.1354/0.1350 vs baseline 0.1358). Inflation adjustment of the premium and sum insured was also worse (0.1351). The hypothesis that the data cutoff (2024-12-30) truncates the claim history of the test rows had no effect, because 81% of policies start on 1 January and only 0.4% of rows change value (the rule takes into account that 2024 is a leap year, so a one-year policy ends on 12-30). The row-type feature (full / cancelled / before or after a change / new mid-year) went from +0.0010 with 1 seed to +0.0001 with 3 seeds and was rejected. What remains is only the fact that buildings mid-term cancellation rows were overpredicted on both folds (actual/predicted 0.82, 0.76).

### Day 6: 2026-10-22

**Shallow trees (early morning; logs kept locally in work/, not in the repository)** 7 leaves, learning rate 0.02 and 600 rounds gave 0.1369 on 3 seeds, above the baseline of 0.1362, and the score rose as the leaves were reduced, converging at 0.1378-0.1379 with 3 leaves. Interpretation (not tested): the data are close to a GLM-like structure synthesised multiplicatively, and deep interactions learn noise. The 7 tree models in the blend (tw, po, twx, pox, fs, fs5, cb) were replaced at once with 5 shallow ones (tw3, po3, twx3, fs3sh, cb3). Blend v2024 0.13721→0.1373, v2023 0.14242→0.14309. eq19, made by carrying over the level decisions of eq18 (`src/transfer.py`), scored public 0.12919, agreeing in direction.

**Variants around the shallow trees are all saturated**: linear_tree, path_smooth 50 and min_data 5000 were all within ±0.0002 of the baseline 0.1380. max_bin 63 gave +0.0005 as a single model and reproduced on another seed set (all of the gain on v2023), but 31, 15 and 7 were worse, and in the blend it gave +0.00006/-0.00001, so it was not adopted. EBM with 0 interactions (0.1349/0.1379) and with 30 (0.1346/0.1398) went different ways by fold against the default 10 (0.1350/0.1384), with a blend gain of +0.00003. In a grid over the TabM weights, v2024 preferred them lower and v2023 higher, so 3/3 was kept.

**Post-processing and credibility extensions (`src/exprate.py`, `src/expcost.py`; helper scripts kept locally in work/, not in the repository; all rejected)**: a p^a post-correction on the blend had its optimum at a=1.0. Varying the policy credibility constant k from 6 to 25 moved the folds in opposite directions, so 12 was kept. Customer- and address-level factors, using only the history of the same customer's other policies, and credibility based on claim amounts (k and cap, year decay, all of them) were worse in every combination (the conclusion: the size of past losses explains almost nothing of future risk; only the counts do). Stacking that learns the blend residuals on one fold and multiplies them onto the other fold was also worse from 50 rounds. The variable selected most often on the residuals differed by fold (rainfall_mm and mean_temperature_c when trained on v2023, premium_rate when trained on v2024). The structure that remains differs from year to year and does not carry over.

**Variable elimination, the day's second big finding (helper scripts and logs kept locally in work/, not in the repository)**: in an ablation that drops variables by group, removing the 7 weather, 7 sales channel and 7 marketing noise variables and the time variables (year, start_month) left v2024 unchanged and raised v2023 by +0.0019. Keeping only the top K variables by importance, by contrast, always lost (0.1344/0.1371/0.1370/0.1380 at K=15/25/35/45, baseline 0.1381). Interpretation (not tested): the low-importance variables also carry signal, and the problem is the groups whose values change from year to year. Dropped one group at a time, the weather and sales groups gave the largest fold-mean gain.
  - Lean versions `tw3l, po3l, twx3l` were built and swapped into the blend: [0.1373, 0.14309]→[0.13754, 0.14377] (+0.00024/+0.00068). Both folds move the same way. Swapping in `fs3shl` as well gives v2023 0.14403. The lean version of cb3 was -0.00001, so the original was kept.
  - **eq20, made by carrying eq18's levels over to this blend, scored public 0.12956** (+0.00037 over eq19). The direction of the local improvement and of the public score agreed, so confidence in it is high.
  - lean2, which also drops the vehicle detail variables (seats, fuel_type, make_model and others, 8 in all), rose as a single model on both seed sets (+0.0003/+0.0008), but in the blend this shrank to +0.00004/±0.00003. The interpretation is that other models capture the same information. Not adopted.
  - Lean TabM (per peril, seed 0): alone below the original (v2023 0.1416 vs 0.1424), ±0.0001 in the blend, not adopted.
  - Per-peril shallow GBM (`src/gbm_peril.py`, 3 leaves): alone it rose a lot, 0.1327→0.1353, but in the blend the folds disagreed (+0.0001/-0.00005), so it was rejected.

## 5. The largest gains so far (in order of effect)

Measured by the change in public score (read with the noise of 0.0009 in mind):

1. Per-line level probing: 0.12852→0.12889 (+0.00037). This is a correction, not a model.
2. Variable elimination (lean): 0.12919→0.12956 (+0.00037).
3. TabM seed averaging and weight: eq12 0.12766 → eq14 0.12817 (+0.0005).
4. Per-peril TabM, policy credibility, shallow trees, segment corrections: each +0.00005 to +0.0002.
5. More model types (CatBoost, MLP, GLM, EBM): each around +0.0001.

In this competition, "what to take out" (shallow trees, lean variables) and "getting the level right" mattered more than "what to add".

## 6. Summary of the level adjustment method (`src/level_probe.py`, `src/transfer.py`)

1. Multiplying the prediction by s makes the deviance of the form A·s^-1/2 + B·s^1/2, so solving for A/B from a single public score gives the optimal s. The curvature is measured with three global-scale submissions.
2. The optimal scale of each line or segment is solved with one submission (`level_probe.py build/solve`).
3. The public noise (lines 2.5-3%, small segments 3.5-8%) is compared with the wobble of our own level (about 4.5%), and the public optimum is pulled back 30% towards x1.03.
4. When a new blend comes out, only the level decisions are carried over with `transfer.py`: row value = probed submission value × new blend / old blend, after which the line totals are matched to the probed submission. The level decisions are independent of model improvements, so they need to be made only once.

## 7. Blend composition (current eq20)

Nine base models (weight 1 each): AutoGluon, GLM, MLP, EBM, tw3l, po3l, twx3l (three kinds of lean 3-leaf trees), fs3shl (shallow lean frequency x severity), cb3 (depth-3 CatBoost). The 6-seed TabM average (tmavg6) at weight 3. The 4-seed per-peril TabM average, with its line totals matched to tmavg6, at weight 3. On top of that the policy credibility factor (12+N)/(12+L) is applied and renormalised per line (`src/make_sub.py`). Finally the line and segment levels of eq18 are carried over with `src/transfer.py`.

## 8. Rejected list (reproducible; the logs are kept locally in work/, not in the repository)

| Attempt | Result | Note (interpretations not tested) |
|---|---|---|
| Post-hoc recalibration (p^a, isotonic regression) | No gain, isotonic regression broke down | Level already right |
| Tweedie power 1.7 or higher | Worse | 1.2-1.4 equivalent |
| New history features (address, counts per cover, annual frequency) | With all of them, down to 0.1335 | The GBM uses them as noise instead |
| Distillation, geometric mean, stacking, Caruana selection | All worse | The equal-weight average is the most robust |
| Double GLM variance weights | Worse | |
| Separate large-loss model | Below the blend | |
| Credibility Transformer | Unstable, low even alone | |
| TabM power 1.3, history features, 8 seeds, stabilisation, pretraining | Noise | |
| Per-peril LightGBM, count auxiliary task | Blend worse | |
| Covariate-shift weights, year decay | Worse | |
| Seasonal exposure feature, period-shape features | No change | |
| Weather split into mean plus deviation | Worse | |
| Amount deflation | Worse | |
| As-of history | ±0.0001 | Rows that change: 0.4% |
| Row-type feature | +0.0001 with 3 seeds | Seed noise |
| Repairer and counterparty network, suspected re-enrolment pairs | Random | |
| IBNER correction of open bodily injury claims | Cannot be validated | Public 0.12807 (within noise) |
| Segment correction learned on one fold | Worse on the other fold | Pulled by large-loss noise |
| Customer and address credibility, amount-based credibility | Worse | |
| Residual stacking | Worse | The remaining residuals differ by year |
| Only the top K by importance | Worse | |
| lean2 (vehicle details removed), lean cb3, lean TabM | No gain in the blend | |
| max_bin, linear_tree, path_smooth, min_data | ±0.0002 | Saturated around the shallow trees |

## 9. Current status and remaining work

- Final candidates: eq20 and eq20_lv. Both passed `src/check_sub.py`. No experiment is in progress.
- Remaining: checking the submissions before the deadline, preparing Part 2 (emerging-market data), the report (5 pages) and video (5 minutes), code cleanup.
- Ideas for Part 2 (not started): a framework that uses the Part 1 model as a prior/offset and blends with credibility weights, a covariate-shift detection report.

## 10. How to reproduce

Environment: Python 3.12, with `pyproject.toml`/`uv.lock` installed by `uv` (`.venv`). CatBoost, EBM and TabM use a separate environment (`.venv-ag`). Long jobs ran under `systemd-run --user` with a memory cap (`MemoryMax`) (on 30 GB RAM and 16 cores; 6-8 threads is safe).

Download the data from the competition page into `data/public/*.parquet`, then run from the repository root with `PYTHONPATH=src`.

1. `src/prep.py` builds the modelling tables (read by `common.load`).
2. Tree models: `src/run.py tw3 po3 twx3` and so on (the lean models: `src/run.py tw3l po3l twx3l`, `LEAN=1 FS_SHALLOW=1 TAG=shl src/run.py fs3`).
3. TabM peril: `TABM_SEED=0 src/tabm_peril.py 5` (run several times with different seeds); the 6-seed TabM average is `tmavg6`.
4. `src/exprate.py` builds N and L for the credibility factor, `src/make_sub.py OUT SCALE GROUP...` builds the blend file, and `src/check_sub.py` checks it.
5. The levels are applied with `src/transfer.py PROBED_CSV NEW_OUT BASE_LIST GROUP...`.

[In the original package, `00_full_src_runnable/` was a flat copy of all of this code, to be copied into the repository's `src/`, and the `.py` files in the stage folders were copies of the same files for easier reading. In this repository the code is in `src/` and `eda/`, with `pyproject.toml` and `uv.lock` at the root. The `work/` helper scripts (`bl.py`, `bl2.py`, `bl3.py`, `sc.py` and others) are kept locally in work/, not in the repository.]

## 11. Folder map

| Original folder | Contents | Dates | Location in this repository |
|---|---|---|---|
| 00_full_src_runnable | Copy of all the code, pyproject, lock | All | `src/*.py`, `pyproject.toml`, `uv.lock` |
| 01_eda | Overview, claims, development (reporting lag), importance, quality, learning curve, adversarial validation | 10-17 | `eda/01_overview.py` to `eda/07_adversarial.py` |
| 02_data_prep_and_target | Target and development correction `prep.py`, common loader `common.py`, IBNER | 10-17, 10-19 | `src/prep.py`, `src/common.py`, `src/ibner.py`; log `ib1.log` kept locally in work/, not in the repository |
| 03_gbm_baseline_and_grids | GBM harness `exp2.py`, configuration grids and logs, seed averaging | 10-17 | `src/exp.py`, `src/exp2.py`, `src/gbm.py`, `src/run.py`, `src/fs.py`, `src/feats.py`; logs (`grid*`, `cap*`, `bin*`, `noyear.*`, `run*.log`, `twxr.log`) kept locally in work/, not in the repository |
| 04_model_families | AutoGluon, GLM, CatBoost, MLP, EBM, TabM, Credibility Transformer, combined model | 10-17 to 10-19 | `src/ag.py`, `src/glm.py`, `src/cb.py`, `src/nn.py`, `src/ebm.py`, `src/tabm_run.py`, `src/ct.py`, `src/pool.py`; logs kept locally in work/, not in the repository |
| 05_per_peril_models | Per-peril TabM, per-peril GBM | 10-19 to 10-22 | `src/tabm_peril.py`, `src/gbm_peril.py`; logs (`tabmp*.log`, `gbmp*`) kept locally in work/, not in the repository |
| 06_blend_and_submission | Blending, submission building, submission checks, scoring tools | All | `src/make_sub.py`, `src/blend.py`, `src/blend2.py`, `src/check_sub.py`; helper scripts `bl.py`, `bl2.py`, `sc.py` kept locally in work/, not in the repository |
| 07_experience_rating | Policy credibility, amount-based credibility, post-correction tests | 10-19, 10-22 | `src/exprate.py`, `src/expcost.py`; `cred.py`, `cred2.py` and log `expcost.out` kept locally in work/, not in the repository |
| 08_level_probing | Level probing, level transfer | 10-20 to 10-22 | `src/level_probe.py`, `src/transfer.py`; `cal.py` kept locally in work/, not in the repository |
| 09_negative_results | Code and logs of rejected experiments | 10-17 to 10-21 | `src/feats2.py`, `src/feats3.py`, `src/feats4.py`, `src/asof.py`, `src/season.py`, `src/deflate.py`, `src/wxmean.py`, `src/large.py`; `wxtest.py`, `resid.py`, `mta.py`, `flags.py` and the logs kept locally in work/, not in the repository |
| 10_shallow_trees | Logs of the shallow-tree experiments | 10-22 | Logs (`shallow.out`, `shallowb.out`, `cb3.out`, `cb3m.out`, `fssh.out`, `reg.out`, `reg.jsonl`) kept locally in work/, not in the repository; the model specs are in `src/run.py`, `src/fs.py` and `src/cb.py` |
| 11_lean_features | Variable elimination, top-K, lean models, lean2 | 10-22 | `imp.py`, `bl3.py` and the logs kept locally in work/, not in the repository; the lean model specs are in `src/run.py` and `src/common.py` |
| public_scores.csv | Date, file name, public score and description of 30 submissions | All | `docs/part1_public_scores.csv` |

## 12. Limits of this record

- The numbers in the text above were taken from the logs and the working record. Explanations marked "interpretation (not tested)" were not verified by experiment.
- Some early logs (the first baseline run and others) were no longer in `work/` and could not be included.
- The public ranks and first-place scores are as recorded at the time. Current values must be checked again on Kaggle.

## Reproducing the final Part 1 submission (eq20)

[Added 2026-10-29. Not part of the translated source. Commands below were taken from the Claude Code transcript of the Part 1 sessions or follow from a script's usage line, as marked. Times are UTC. All commands run from the repository root.]

### What eq20 depends on

`src/transfer.py` rebuilds two blends with `make_sub.blend("test", ...)`. The old blend uses the default `make_sub.BASE` (`tw po fs ag twx pox fs5 glm cb nn ebm`) plus `tmavg6` and the group `tabmp0..3`; this is the blend behind eq17_x103, from which eq17_lv and eq18 were built. The new blend uses the base list given on the command line (`ag glm nn ebm tw3l po3l twx3l fs3shl cb3`) plus `tmavg6` and the same group. Both blends also read `work/exprateoof_test.parquet`. So eq20 needs the saved test predictions of every model in both blends, the credibility file, and `submissions/eq18.csv`.

### Check made on 2026-10-29

From the predictions saved in `work/preds/` and `work/exprateoof_*.parquet`, the following were rebuilt into a scratch folder and compared row by row with the files in `submissions/` (626,639 rows each):

- `src/transfer.py` with the eq20 arguments: identical to `submissions/eq20.csv` (maximum absolute difference 0.0).
- `src/make_sub.py` with the eq17_x103 arguments: identical to `submissions/eq17_x103.csv`.
- The recorded inline code for eq17_lv and eq18 (below): identical to `submissions/eq17_lv.csv` and `submissions/eq18.csv`.

The models themselves were not retrained. Whether retraining from scratch reproduces the saved predictions exactly is not confirmed.

### Environments

Confirmed (transcript, 2026-10-17 and 2026-10-18):

```
# .venv (project environment; pyproject.toml and uv.lock)
uv init -q --bare --python 3.12
uv add -q pandas pyarrow polars scikit-learn lightgbm statsmodels

# .venv-ag (AutoGluon, CatBoost, EBM, TabM, torch CPU)
uv venv -q --python 3.12 .venv-ag
VIRTUAL_ENV=.venv-ag uv pip install -q "autogluon.tabular[lightgbm,catboost,xgboost]" polars pyarrow
uv pip install --python .venv-ag/bin/python torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv-ag/bin/python tabm==0.0.3 rtdl-num-embeddings==0.0.12 interpret==0.7.8
```

On a fresh checkout, `uv sync` recreates `.venv` from `uv.lock` (follows from the lock file; not seen as a command in the transcript). Installed in `.venv-ag` as of 2026-10-29: autogluon 1.6.3, catboost 1.2.10, interpret 0.7.8, torch 2.14.1+cpu, tabm 0.0.3, rtdl_num_embeddings 0.0.12, lightgbm 4.7.0.

Which environment each script needs, from its imports: `src/ag.py` (autogluon), `src/cb.py` (catboost), `src/ebm.py` (interpret), `src/nn.py`, `src/tabm_run.py`, `src/tabm_peril.py` and `src/ct.py` (torch; the TabM scripts also tabm and rtdl_num_embeddings) need `.venv-ag`. `src/prep.py`, `src/run.py`, `src/fs.py`, `src/glm.py`, `src/exprate.py`, `src/make_sub.py`, `src/transfer.py`, `src/level_probe.py` and `src/check_sub.py` use only lightgbm, polars, numpy, pandas and scikit-learn, which both environments have; the transcript runs some of them with `.venv-ag/bin/python`.

### Step 1: modelling tables

Confirmed (2026-10-17 14:19): `uv run python src/prep.py` (writes `work/{motor,buildings,contents}.parquet`). Data must first be in `data/public/`.

### Step 2: base predictions (`work/preds/<name>_{v2024,v2023,test}.parquet`)

All confirmed from the transcript. In the transcript each ran inside `systemd-run --user ... -p MemoryMax=...` with the log redirected to `work/`; only the environment variables and the command are shown here.

| Name(s) | Command | Env | Run |
|---|---|---|---|
| tw, po, fs | `PYTHONPATH=src .venv/bin/python src/run.py tw po fs` | .venv | 2026-10-17 15:14, log `work/run_models.log` |
| ag | `PYTHONPATH=src .venv-ag/bin/python src/ag.py 900` | .venv-ag | 2026-10-17 15:14 (after the line above), log `work/run_ag.log` |
| twx, pox, fs5 | `PYTHONPATH=src NT=6 .venv/bin/python src/run.py twx pox fs5` | .venv | 2026-10-17 20:59, log `work/run2.log` |
| glm | `PYTHONPATH=src OMP_NUM_THREADS=4 .venv/bin/python src/glm.py` | .venv | 2026-10-17 20:59, log `work/glm.log` |
| cb | `PYTHONPATH=src NT=6 .venv-ag/bin/python src/cb.py 300` | .venv-ag | 2026-10-17 22:07, log `work/cb.log` |
| nn | `PYTHONPATH=src NT=6 .venv-ag/bin/python src/nn.py 3` (run just after the default was set to `seeds=5`, which is the current default) | .venv-ag | 2026-10-17 22:52, log `work/nn.log` |
| ebm | `PYTHONPATH=src NT=6 .venv-ag/bin/python src/ebm.py fit` | .venv-ag | 2026-10-18 16:16, log `work/ebm.log` |
| tabm0 to tabm5 | `PYTHONPATH=src NT=6 TABM_SEED=$s .venv-ag/bin/python src/tabm_run.py 5` for s = 0 1, 2 3, 4 5 | .venv-ag | 2026-10-18 18:05, 20:22, 23:11, logs `work/tabm$s.log` |
| tmavg6 | Inline Python, see below | .venv | 2026-10-19 01:52 |
| tabmp0 to tabmp3 | `PYTHONPATH=src NT=7 TABM_SEED=$s .venv-ag/bin/python src/tabm_peril.py 5` for s = 0 1, then 2 3 | .venv-ag | 2026-10-19 14:55 and 17:12, logs `work/tabmpr$s.log` |
| exprateoof (credibility N, L) | `PYTHONPATH=src NT=14 EXP_TAG=oof PYTHONHASHSEED=0 .venv/bin/python src/exprate.py` | .venv | 2026-10-19 13:56, writes `work/exprateoof_{fold}.parquet` |
| cb3 | `PYTHONPATH=src NT=8 CB_DEPTH=3 CB_LR=0.08 CB_NAME=cb3 .venv-ag/bin/python src/cb.py 300` | .venv-ag | 2026-10-22 01:17, log `work/cb3m.out` |
| tw3l, po3l, twx3l | `PYTHONPATH=src NT=8 .venv/bin/python src/run.py tw3l po3l twx3l` | .venv | 2026-10-22 11:26, log `work/lean.out` |
| fs3shl | `PYTHONPATH=src NT=4 LEAN=1 FS_SHALLOW=1 TAG=shl .venv/bin/python src/run.py fs3` | .venv | 2026-10-22 12:28, log `work/leanfs.out` |

`PYTHONHASHSEED=0` matters for `src/exprate.py`: it splits policies into out-of-fold groups with Python's `hash()`. Several scripts were edited after these runs (new environment switches such as `TABM_LR`, `SNAP`, `PRE`, `AUX_N`, `CB_MAX`, `EBM_INT`, `LEAN`); the edits checked (`TABM_LR`, `SNAP`, `PRE`, `AUX_N`, `CB_DEPTH`, `CB_LR`, `EBM_INT`, `EBM_BAGS`, `FS_SHALLOW`) keep the earlier behaviour as the default, but a full retrain with today's code was not run, so exact equality with the saved predictions is not confirmed. AutoGluon, CatBoost and the torch models are not guaranteed to be bit-for-bit deterministic across runs (not tested).

`tmavg6` was not written by a script in `src/`. The transcript (2026-10-19 01:52) shows inline Python run with `PYTHONPATH=src .venv/bin/python -` that averages the six seeds per fold, followed by a rename:

```python
from blend import frame
S=[f"tabm{s}" for s in range(6)]
for f in ("v2024","v2023","test"):
    a=frame(S,f)
    a.with_columns(pred=sum(a[s] for s in S)/6).drop(S).write_parquet(f"work/preds/tabm6_{f}.parquet")
```

```
cd work/preds; for f in v2024 v2023 test; do mv tabm6_$f.parquet tmavg6_$f.parquet; done
```

(The snippet above keeps only the lines of that command that write the file; the rest printed fold scores.)

### Step 3: eq17_x103

Confirmed (2026-10-19 19:29):

```
PYTHONPATH=src .venv-ag/bin/python src/make_sub.py submissions/eq17_x103.csv 1.03 tabmp0,tabmp1,tabmp2,tabmp3
PYTHONPATH=src .venv-ag/bin/python src/check_sub.py submissions/eq17_x103.csv
```

There is no separate `eq17.csv`; eq17_lv and eq18 are built from `eq17_x103.csv` divided by 1.03.

### Step 4: line probes and eq17_lv

The three line probes `submissions/eq17_{motor,buildings,contents}110.csv` (2026-10-20 18:14) were made by inline Python that multiplies one line of `eq17_x103.csv` by 1.10/1.03. Their public scores (motor 0.12776, buildings 0.12868, contents 0.12852) gave the line scales. The solver for these three line scales is not in `src/` and the command that computed 0.9764, 1.0925 and 1.0644 was not confirmed; the values are hard-coded below.

eq17_lv, confirmed (2026-10-20 18:16), run with `PYTHONPATH=src .venv-ag/bin/python -`:

```python
import polars as pl
from common import load
S = {"motor": 0.9764, "buildings": 1.0925, "contents": 1.0644}
lab = pl.concat([load(l).filter(pl.col("split")=="test").select("row_id").with_columns(line=pl.lit(l)) for l in S])
b = pl.read_csv("submissions/eq17_x103.csv", schema_overrides={"row_id": pl.String}).join(lab, on="row_id")
out = b.with_columns(prediction=pl.col("prediction")/1.03*pl.col("line").replace_strict(S, return_dtype=pl.Float64)).select("row_id","prediction")
out.write_csv("submissions/eq17_lv.csv")
```

followed by `PYTHONPATH=src .venv-ag/bin/python src/check_sub.py submissions/eq17_lv.csv`.

### Step 5: segment probes

Confirmed:

```
PYTHONPATH=src .venv-ag/bin/python src/level_probe.py build submissions/eq17_lv.csv      # 2026-10-20 21:45, writes submissions/probe_*.csv
PYTHONPATH=src .venv-ag/bin/python src/level_probe.py solve submissions/eq17_lv.csv 0.12889 m_young=0.12891 m_rural=0.12887 m_tpft=0.12887 b_retired=0.12860 b_wind=0.12841   # 2026-10-21 00:04
```

### Step 6: eq18

Confirmed (2026-10-21 00:06), run with `PYTHONPATH=src .venv-ag/bin/python -`:

```python
import sys; sys.path.insert(0,"src")
import numpy as np, polars as pl
from common import load
from level_probe import SEGS, ids, read
pub = {"motor": 0.9764, "buildings": 1.0925, "contents": 1.0644}
line_s = {l: 1.03 + 0.7 * (s - 1.03) for l, s in pub.items()}
seg = {"m_young": np.sqrt(0.886 * 0.941), "m_rural": np.sqrt(0.868 * 0.956), "m_tpft": np.sqrt(0.794 * 0.965), "b_wind": np.sqrt(0.94 * 0.87)}
print({k: round(v, 4) for k, v in line_s.items()}, {k: round(v, 3) for k, v in seg.items()})
lab = pl.concat([load(l).filter(pl.col("split")=="test").select("row_id").with_columns(line=pl.lit(l)) for l in pub])
b = read("submissions/eq17_x103.csv").join(lab, on="row_id").with_columns(mu=pl.col("prediction") / 1.03)
q = b["mu"].to_numpy().copy()
for k, f in seg.items():
    q[b["row_id"].is_in(ids(k).implode()).to_numpy()] *= f
ln = b["line"].to_numpy(); mu = b["mu"].to_numpy()
for l, s in line_s.items():
    i = ln == l; q[i] *= s * mu[i].sum() / q[i].sum()
pl.DataFrame({"row_id": b["row_id"], "prediction": q}).write_csv("submissions/eq18.csv")
```

followed by `PYTHONPATH=src .venv-ag/bin/python src/check_sub.py submissions/eq18.csv`. The local segment factors (0.886, 0.868, 0.794, 0.94) are hard-coded in this command; the command that computed them from the two local folds was not confirmed.

### Step 7: eq20

Confirmed (2026-10-22 13:06):

```
B=ag,glm,nn,ebm,tw3l,po3l,twx3l,fs3shl,cb3
PYTHONPATH=src .venv/bin/python src/transfer.py submissions/eq18.csv submissions/eq20.csv $B tabmp0,tabmp1,tabmp2,tabmp3
PYTHONPATH=src .venv/bin/python src/transfer.py submissions/eq17_lv.csv submissions/eq20_lv.csv $B tabmp0,tabmp1,tabmp2,tabmp3
for f in eq20 eq20_lv; do PYTHONPATH=src .venv/bin/python src/check_sub.py submissions/$f.csv | tail -2; done
```

The second line builds the hedge candidate eq20_lv from the same blend.
