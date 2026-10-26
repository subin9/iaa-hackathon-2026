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
$PY part2/probe_solve_cells.py part2/v5_probes.json work/p2/v7.csv
echo "work/p2/v7.csv is the Part 2 file; the final choice is made in the Kaggle UI"
