# Target construction notes — structure

1. **Target definition** as implemented (which claims, which amounts,
   repudiated treatment, valuation date), and reconciliation: sum of `y`
   across modelling tables vs net incurred in the cleaned claims table.
2. **Claim–policy linkage**: method, match rate, treatment of unmatched
   claims.
3. **Completion (IBNR)**: how the report-lag curve was built (years,
   weighting, per-peril mixing), how the row-level completion factor is
   computed, and — explicitly — which part of the curve is observed in
   this market and which part is borrowed or assumed, with the effect on
   2024 completion by line.
4. **Trend**: fit years, functional form, extrapolated 2025 factor by line,
   and why those years.
5. **Large losses**: cap level, number of claims affected, redistribution
   multiplier by line.
6. **Open-claim adequacy (IBNER)**: what you compared, what you saw, what
   you did (and did not) adopt, and why.
7. **Resulting target level by line and year** (y per exposure-year, before
   and after completion/trend), with the raw burning cost next to it.
8. **Known limitations** of the target.
