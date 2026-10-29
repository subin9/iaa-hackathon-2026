#!/usr/bin/env bash
# Rebuild the Part 2 submission from the raw competition files. Run from the repo root.
# Needs: data/part2/{developed,emerging}/*.parquet (competition download), the project venv (uv sync), 16 GB RAM, about 40 minutes on 8 cores.
set -euo pipefail
export PYTHONPATH=src:part2 NT=${NT:-8}
PY=.venv/bin/python

# 1. Part 1 tables for the developed market: src/prep.py reads data/public (the Part 1 download, identical to data/part2/developed) and writes work/{line}.parquet
[ -f work/motor.parquet ] || $PY src/prep.py

# 2. emerging tables and the developed tables on the emerging coding
$PY part2/prep_emerging.py
$PY part2/harmonize.py

# 3. developed-market per-peril priors: three variants, vehicle details left out, new_business kept
export P2_KEEP=new_business P2_DROP=make_model,engine_size_cc,seats,body_type,transmission,fuel_type,driver_assist,vehicle_colour
P2_TAG=_v_tw $PY part2/devprior_peril.py
P2_TAG=_v_po P2_VARIANT=poisson $PY part2/devprior_peril.py
P2_TAG=_v_ex P2_VARIANT=extra $PY part2/devprior_peril.py
$PY part2/average_priors.py _v_tw _v_po _v_ex _v_avg

# 4. checks, validation numbers, submission
$PY -m pytest part2/tests -q
$PY part2/report_numbers.py
$PY part2/fit_final.py work/p2/sub_final_base.csv
cp work/p2/sub_final_base.csv work/p2/sub_v4.csv

# 5. v5: the transferred new-business and renewal multipliers (part2/v5_args.txt, one segment spec and factor per line)
mapfile -t V5 < part2/v5_args.txt
$PY part2/probe.py work/p2/sub_v4.csv work/p2/v5_full.csv "${V5[@]}"

# 6. v7: leaderboard probes on v5 (q5a..q5h.csv were built with part2/probe.py; their scores are in part2/v5_probes.json and part2/probes.json),
#    sampling noise of the segment factors from the out-of-fold training rows, then twelve cell factors with a ridge prior, shrunk by that noise
$PY part2/e13_cell_noise.py
P2_NO_CONSTANT=1 $PY part2/probe_solve_cells.py part2/v5_probes.json work/p2/v7.csv   # the submitted v7
$PY part2/probe_solve_cells.py part2/v5_probes.json work/p2/v8.csv                    # same with the deviance constant (scores the same, not submitted)


# 7. v9 (submitted 2026-10-26, public 0.17303): the prior average with the Tweedie 1.6 variant in place of 1.4 (e17, e20), carried to v7's twelve cell totals
P2_TAG=_x_p16 P2_POWER=1.6 $PY part2/devprior_peril.py
$PY part2/average_priors.py _x_p16 _v_po _v_ex _x_avg16
$PY part2/fit_final.py work/p2/sub_v4_p16.csv --tag _x_avg16
$PY part2/transplant_cells.py work/p2/v7.csv work/p2/sub_v4_p16.csv work/p2/v9.csv

# 8. v10 (submitted 2026-10-28, public 0.17247): the teammate's cleaned emerging files (unzipped to data/part2_cleaned) built in a separate tree, the teammate's
#    feature list in all three priors (renewal_count and vehicle details kept), carried to v7's twelve cell totals (e21)
R=work/clean; mkdir -p $R/work/p2 $R/data/part2
ln -sfn ../../src $R/src; ln -sfn ../../part2 $R/part2; ln -sfn ../../.venv $R/.venv
ln -sfn ../../../../data/part2/developed $R/data/part2/developed; ln -sfn ../../../../data/part2_cleaned $R/data/part2/emerging
for l in motor buildings contents; do ln -sfn ../../../work/$l.parquet $R/work/$l.parquet; done
(cd $R && $PY part2/prep_emerging.py && $PY part2/harmonize.py
 for v in "_tm_p16 P2_POWER=1.6" "_tm_po P2_VARIANT=poisson" "_tm_ex P2_VARIANT=extra"; do set -- $v
   env P2_KEEP=new_business,renewal_count P2_DROP=make_model,vehicle_colour,compulsory_excess P2_TAG=$1 $2 $PY part2/devprior_peril.py; done
 $PY part2/average_priors.py _tm_p16 _tm_po _tm_ex _tm_avg
 $PY part2/fit_final.py work/p2/sub_v4_tm.csv --tag _tm_avg)
$PY part2/transplant_cells.py work/p2/v7.csv $R/work/p2/sub_v4_tm.csv work/p2/v10.csv

# 9. v11 (submitted 2026-10-28, public 0.17184, rejected): v10's base times a motor residual booster (e23), carried to v7's cell totals
(cd $R && $PY part2/residual_motor.py work/p2/sub_v4_tm.parquet work/p2/sub_v4_tm_rb.csv --tag _tm_avg)
$PY part2/transplant_cells.py work/p2/v7.csv $R/work/p2/sub_v4_tm_rb.csv work/p2/v11.csv

# 10. v12c (submitted 2026-10-28, public 0.17333): buildings fire on wildfire_index with the developed-market slope on v10's prior (e25), then the geometric
#     mean of v9 and v10 times that fire term, carried to v7's cell totals
(cd $R && $PY part2/fire_term.py _tm_avg _wf_avg && $PY part2/fit_final.py work/p2/sub_v4_wf.csv --tag _wf_avg)
$PY part2/transplant_cells.py work/p2/v7.csv $R/work/p2/sub_v4_wf.csv work/p2/v12a.csv
$PY part2/geo_mean.py work/p2/v9.csv work/p2/v10.csv work/p2/v12c_raw.csv work/p2/v12a.csv work/p2/v10.csv
$PY part2/transplant_cells.py work/p2/v7.csv work/p2/v12c_raw.csv work/p2/v12c.csv

# 11. v13_cells (submitted 2026-10-29, public 0.17556, final): x1.2 probes on seven motor segments of v10 (q12a..q12h; q12d not submitted, scores in
#     part2/q12_probes.json, which reads the submitted v10 from work/p2/submitted), solved one by one and shrunk by sampling noise, applied to v12c,
#     carried to v7's cell totals (v13_raw, the same without the last step, scored 0.17552)
mkdir -p work/p2/q12 && $PY part2/probe_q12.py work/p2/v10.csv work/p2/q12
$PY part2/probe_overlays.py part2/q12_probes.json work/p2/v12c.csv work/p2/v13_raw.csv
$PY part2/transplant_cells.py work/p2/v7.csv work/p2/v13_raw.csv work/p2/v13_cells.csv

# 12. office premium of the 20 reference policies from the final file (part2/final.json), figures, report and slides
$PY -c "import polars as pl; pl.read_csv('work/p2/v13_cells.csv').write_parquet('work/p2/final.parquet')"
$PY part2/office_premium.py work/p2/final.parquet work/p2/office_final.csv
$PY part2/report/figures.py
$PY part2/report/build_report.py work/p2/office_final.csv
$PY part2/video/slides.py
echo "final Part 2 file: work/p2/v13_cells.csv; the final selection is made in the Kaggle UI"
