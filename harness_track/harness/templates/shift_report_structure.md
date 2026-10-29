# Shift report — structure

1. **Schema differences.** Columns only in developed, only in emerging,
   same name but different encoding or meaning. Proposed mapping (link to
   schema_mapping.md).
2. **Emerging train vs emerging test.** For every shared column: a
   distribution-distance measure (PSI or equivalent) and the top shifts,
   each interpreted as (a) portfolio-mix change, (b) data-definition
   change, or (c) time/identity leakage. Pay attention to new-business
   share, channel, tenure/renewal counts, age mix, region mix.
3. **Developed vs emerging (training years).** Same columns; which
   differences are mix and which look like different risk behaviour.
4. **Frequency, severity and peril mix by line**, per exposure-year, for
   developed and emerging training years side by side (raw, before IBNR
   adjustment, state the valuation date). Where counts are thin, say so.
5. **Acquired-portfolio check.** Within emerging training data, compare the
   broker / new-business segment with the rest on frequency and severity;
   state whether the 2025 book can be assumed to behave like the renewal
   book.
6. **Leakage checks.** Adversarial validation (train latest year vs test)
   and any column whose distribution exists only in training.
7. **Implications for modelling.** Three to eight bullets: what to drop,
   what to re-estimate, what to borrow, what to watch.
