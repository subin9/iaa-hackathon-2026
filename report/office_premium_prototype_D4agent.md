# Office premium build-up — 20 reference policies

Risk premiums from `submission.csv`. Loadings from `expenses.parquet` (emerging): fixed 85 CU per policy-year (pro-rated by exposure), variable 15%, commission direct 0% / broker 20% / comparison site 10% (undefined for the emerging market — developed value assumed, team query F-19), premium tax 8%, cat reinsurance 12% of property risk premium, target profit 8%.

Office premium P = (risk + cat + fixed) / (1 − variable − commission − tax − profit). All CU, row totals for the row's exposure.

| row_id | line | exposure | channel | NB | risk premium | + cat | + fixed | = net cost | office premium | per year | office / risk |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| B00215707 | buildings | 0.9863 | broker | Y | 253.34 | 30.40 | 83.84 | 367.58 | **750.15** | 760.57 | 2.96 |
| B00215809 | buildings | 0.9753 | direct | Y | 385.34 | 46.24 | 82.90 | 514.48 | **745.63** | 764.51 | 1.93 |
| B00217584 | buildings | 0.9671 | broker | Y | 1,543.75 | 185.25 | 82.20 | 1,811.20 | **3,696.33** | 3,822.07 | 2.39 |
| B00218282 | buildings | 0.9726 | broker | Y | 286.33 | 34.36 | 82.67 | 403.36 | **823.19** | 846.38 | 2.87 |
| B00223369 | buildings | 0.9945 | broker | Y | 855.35 | 102.64 | 84.53 | 1,042.53 | **2,127.61** | 2,139.38 | 2.49 |
| B00229821 | buildings | 0.9918 | broker | Y | 362.87 | 43.54 | 84.30 | 490.72 | **1,001.46** | 1,009.74 | 2.76 |
| B00250679 | buildings | 0.1096 | broker | Y | 18.55 | 2.23 | 9.32 | 30.09 | **61.41** | 560.35 | 3.31 |
| C00259568 | contents | 1.0000 | broker | N | 33.70 | 4.04 | 85.00 | 122.75 | **250.51** | 250.51 | 7.43 |
| C00270331 | contents | 0.9726 | broker | Y | 48.82 | 5.86 | 82.67 | 137.35 | **280.31** | 288.20 | 5.74 |
| C00283470 | contents | 0.9726 | broker | Y | 52.04 | 6.24 | 82.67 | 140.96 | **287.67** | 295.77 | 5.53 |
| C00286287 | contents | 0.9671 | broker | Y | 188.48 | 22.62 | 82.20 | 293.30 | **598.58** | 618.94 | 3.18 |
| C00302985 | contents | 0.9918 | broker | Y | 60.32 | 7.24 | 84.30 | 151.86 | **309.92** | 312.48 | 5.14 |
| C00314425 | contents | 0.0685 | broker | Y | 4.59 | 0.55 | 5.82 | 10.96 | **22.37** | 326.55 | 4.88 |
| M00118569 | motor | 0.9397 | direct | N | 751.41 | 0.00 | 79.87 | 831.28 | **1,204.76** | 1,282.06 | 1.60 |
| M00129413 | motor | 0.3315 | broker | Y | 124.14 | 0.00 | 28.18 | 152.32 | **310.86** | 937.73 | 2.50 |
| M00153851 | motor | 0.9616 | broker | Y | 400.22 | 0.00 | 81.74 | 481.96 | **983.59** | 1,022.86 | 2.46 |
| M00161473 | motor | 0.9644 | broker | Y | 732.90 | 0.00 | 81.97 | 814.87 | **1,663.00** | 1,724.39 | 2.27 |
| M00167496 | motor | 0.9836 | broker | Y | 572.65 | 0.00 | 83.61 | 656.26 | **1,339.31** | 1,361.64 | 2.34 |
| M00176777 | motor | 0.9918 | broker | Y | 804.53 | 0.00 | 84.30 | 888.83 | **1,813.94** | 1,828.93 | 2.25 |
| M00185311 | motor | 0.9644 | direct | Y | 729.29 | 0.00 | 81.97 | 811.26 | **1,175.74** | 1,219.14 | 1.61 |

Totals by line: buildings n=7 risk 3,706 → office 9,206 (×2.48); contents n=6 risk 388 → office 1,749 (×4.51); motor n=7 risk 4,115 → office 8,491 (×2.06)

Worked example (first motor row): office = (risk + 0 + 85 × exposure) / (1 − 0.15 − commission − 0.08 − 0.08); for a broker policy the denominator is 1 − 0.15 − 0.20 − 0.08 − 0.08 = 0.49, so every CU of net cost needs 2.04 CU of office premium; a direct policy's denominator is 0.69.

Notes: (1) the risk premium is the model's expected ultimate claim cost for the row — it already includes IBNR completion, the trend decision and the new-business relativity (report/decisions_B.md); (2) cat reinsurance applies to property risk premium only, as the expenses table states; (3) a very short row (exposure 0.07–0.33) carries a pro-rated fixed expense — if the insurer charges the fixed expense per policy regardless of term, those rows' office premiums rise by (1 − exposure) × 85 / denominator.
