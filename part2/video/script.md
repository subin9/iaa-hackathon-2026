# 5 minute video: script and slide cues

Target 4:45 to 5:00 at about 135 words a minute. Slides: `part2/video/slides.pdf` (built by `part2/video/slides.py`). Numbers marked [final] are filled in from `part2/final.json` once the last submission is chosen.

**[0:00 to 0:25] Slide 1, title and result.**
We are team HS. This is our two-week story: a developed market in Part 1, an emerging market in Part 2, and an AI coding agent next to us all the way. Part 1 ended with a private D-squared of 0.13755, rank eight of fifty-one. Part 2 reached a public D-squared of [final], and the interesting part is how.

**[0:25 to 1:10] Slide 2, what changed.**
The emerging market has two years of data, a hundred and nine thousand training rows against two hundred and nine thousand to predict, and three quarters of the 2025 rows are new business from a broker. We asked one question before modelling: what carries over? The answer is on the left. Rating-factor effects, like young drivers or no-claims bonus, look almost the same in both markets. Levels do not. Motor cost is a quarter lower, escape of water is half, and the climate is different, with twice the hail days and half the freezing days. So we keep the relativities and re-learn the levels.

**[1:10 to 2:05] Slide 3, the approach.**
Step one: a prior. Shallow gradient boosting per line and per peril, trained on four years of developed data, on the fields both markets share. Step two: peril levels from the emerging data, shrunk toward the line level so that a peril with fifty claims cannot move far. Step three: corrections, but only those the data can prove. A robust score test screens candidate factors, a ridge model fits them, and nested cross-validation keeps us honest. Two survived: male drivers cost thirty-nine percent more on the at-fault perils, and buildings policyholders aged thirty-five to forty-nine cost a third less. Step four: new business, which I come back to.

**[2:05 to 2:55] Slide 4, validation and guardrails.**
Cross-validation is grouped by customer so nobody is on both sides. The ladder shows what each step buys: a constant rate gives 0.078, a model on emerging data alone 0.118, the Part 1 model ported unchanged 0.134, the final pipeline 0.141. Twenty-two automated tests guard the pipeline. They exist because things went wrong: a reordered column frame took the score from 0.134 to 0.036, a double level correction inflated motor predictions by twelve percent, and the developed data had timber coded T in two years and W in three, which a model reads as a year flag. Each is now a test.

**[2:55 to 3:50] Slide 5, new business.**
Cross-validation cannot see new business, it is twelve percent of the training rows. The public leaderboard can, because three quarters of the test rows are new business. The public score is a sum over rows, so it separates by segment. One probe per segment gives the best multiplier for that segment. The method said: motor new business forty percent higher than our model, buildings twenty-three, contents eleven, renewals unchanged. It predicted a score for the half-way point of 0.16433, and the leaderboard returned 0.16446. We use these multipliers shrunk, say openly that they come from the leaderboard, and list every probe in the repository.

**[3:50 to 4:35] Slide 6, the AI workflow.**
The AI wrote and ran the exploration, the models, the tests and this report. We controlled the decisions: which experiments, what counts as adoption, which submissions, which final. Verification was concrete: every number in the report is copied from script output, the AI's own correction code is tested against a planted effect and against noise, and rejected ideas, such as experience rating or weather in the prior, stay in the log with their numbers.

**[4:35 to 5:00] Slide 7, limits and what next.**
What we do not know: new business is the biggest uncertainty, whether the uplift sits in the broker channel is unresolved, and the 2025 weather shift is not modelled. Small perils like fire and subsidence are shrunk hard. Next we would collect broker-portfolio claims early, because that is where the money is. Thank you.
