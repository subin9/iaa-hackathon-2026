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
echo "next: apply the new-business multipliers with part2/probe.py (see part2/probes.json and README) and submit"
