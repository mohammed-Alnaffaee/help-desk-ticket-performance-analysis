# Help Desk Tickets — Domain III Conditional Measurement (v0.3)

Run locally from this folder with Python 3 and `pandas`, `numpy` installed:

```bash
python helpdesk_domain3_measurement.py "/absolute/path/Help Desk Tickets.zip" "./output"
python -m unittest test_domain3_measurement.py -v
```

The two Python source files in this directory are needed: `helpdesk_domain3_measurement.py` and its self-contained stage-reconciliation helper `helpdesk_timeline_qa.py`. Tests do not require the dataset. Original ZIP is read-only and unchanged. Re-running produces CSVs and `validation_summary.json`; the bundled outputs are precomputed snapshots.

| File | What it contains |
|---|---|
| `ticket_outcomes_conditional.csv` | All 19,714 ticket outcomes, A/B clock values, timestamps, censor status, QA flags and hypothetical cutoff sensitivity |
| `observed_status_intervals.csv` | 81,931 positive observed event intervals (no extension to source `ended` for primary measurement) |
| `exceptions_and_censored.csv` | All exceptions/flags and withheld cases (not all flagged cases excluded if a breach predated ambiguity) |
| `top30_AB_outliers.csv` | Large A/B duration gaps for manual review |
| `conditional_annual_counts.csv` | Year-level counts and **conditional** rates; historical only |
| `validation_summary.json` | Reproduced totals and definitions |
| `Cleaning_and_Transformation_Rules.md` | Cleaning/transformation decisions, exception disposition, denominator and validation gates |
| `DomainIV_Methodology_Decision.md` | Method selection and next executable SQL/Power BI steps |
| `HelpDesk_Decisions_and_DQ_Gate_v0.3.md` | Versioned decision log; latest addendum supersedes ended-bound metrics |
| `test_domain3_measurement.py` | 14 synthetic unit tests |

**Do not present 44.1826% as an official company KPI.** It is the conditional ratio 8,662 observed-event, policy-B confirmed breaches divided by 19,605 evaluable tickets; 109 censored/indeterminate excluded. No verified extraction timestamp exists. `pending_customer_approval` pause and company policy still need Proxy confirmation; no contractual SLA is evidenced.
