# Help Desk Ticket Performance Analysis

A practical, end-to-end **descriptive and diagnostic analytics** portfolio project built with **Python, PostgreSQL (SQL), and Power BI**. It examines historical external-project help-desk tickets created during **2019–2022** to understand which tickets exceeded a project-defined **72-hour operational target**, and where follow-up investigation may be useful.

> **Measurement note:** The reported 44.18% is a **conditional analytical rate**: the number of confirmed breaches divided by tickets whose outcomes could be reliably classified under the project's working rules. It is **not** a verified contractual SLA, a company-approved KPI, or a claim about current performance.

## Business question

Among in-scope tickets, which ones **ever exceeded 72 accumulated, countable hours before reaching `closed`**, including those later closed, and where do confirmed breaches concentrate by time period, ticket type, project, priority, and workflow state?

## Data and grain

- **Scope:** External projects (`issue_proj` code length > 6, as defined in source metadata), issue types `Ticket`, `Service`, `HD Service`, creation years **2019–2022**.
- **Ticket grain:** `issues.csv` → one record per issue ID.
- **Event grain:** `issues_change_history.csv` → status and other changes across time.
- **Other source files:** `issues_snapshot.csv` (not safe to join naively at ticket grain), `sample_utterances.csv` (sampled communications; not a satisfaction survey).
- **Scoped population:** **19,714** tickets. The 2023 data was not included because the available period is incomplete.

## KPI and headline result

| Metric | Value |
|---|---:|
| In-scope tickets | 19,714 |
| Confirmed breached tickets | 8,662 |
| Closed without proven breach | 10,943 |
| Evaluable tickets | 19,605 |
| Excluded censored/indeterminate tickets | 109 |
| **Conditional 72-hour breach rate** | **44.1826%** |

**Closure-based counting (Rule B; working assumption):** Count cumulative nonpaused time after creation until entering `closed`; `resolved` remains countable. Pause during `waiting`; `pending_customer_approval` is a provisional project rule awaiting proxy confirmation. Time can resume after reopening. A breach is **strictly greater than 72 counted hours at any observed point while the ticket is not closed**, even if it later closes. **Resolution-based counting (Rule A)** (stop counting at `resolved`) is retained only for sensitivity analysis.

Where the event evidence is insufficient for a definite outcome, tickets are labeled censored or indeterminate—not assumed to have met the target. A verified extraction timestamp and signed operational measurement policy are unavailable.

## Key findings

- Annual conditional breach rate: **43.12% (2019)**, **47.99% (2020)**, **47.74% (2021)**, **39.18% (2022)**. 2022 reweighted to the 2021 evaluable ticket-type mix is **39.88%**; type mix alone does not account for the observed decline.
- `HD Service` has the highest conditional breach rate (**58.64%**), but `Ticket` has the largest number of confirmed breaches (**6,607**).
- Projects `C06hgfz_x` (**333/434; 76.73%**) and `C06hqzcz0` (**170/200; 85.00%**) warrant focused investigation; type-specific comparisons confirm their elevated rates are not purely ticket-mix effects.
- Among already-breached tickets with positive state time, median counted hours are notably high in `pending_deployment` (**414.16h**) and `validation` (**290.42h**). These durations **do not equal staff working hours** and do not establish causation.

For fuller evidence, caveats and candidate decisions, see [`docs/Findings_and_Recommendations.md`](docs/Findings_and_Recommendations.md).

## Approach and tools

1. **Problem framing:** Define the 72-hour operational question, decision context, population, and unverified counting assumptions.
2. **Python preparation:** Mixed-format UTC timestamp parsing, event ordering, status timeline reconstruction, A/B comparison, censoring, data-quality flags and synthetic tests.
3. **PostgreSQL SQL:** Stage exports; reconcile tickets, classifications and interval hours; analyze year, issue type, priority, projects and workflow; perform final quality gates.
4. **Power BI Desktop:** Two imported SQL views with an active, single-direction many-to-one relationship on `ticket_id`. DAX measures show volume, evaluable denominator, confirmed breaches, conditional rate and excluded cases.
5. **Communication:** Historical decision-oriented dashboard and documented non-causal recommendations, not a deployed corporate product.

**Report pages:**

- `Executive Overview`: five KPI cards, annual and issue-type rates, Top 10 projects by confirmed breach count, slicers.
- `Operational Deep Dive`: median counted workflow-state duration, number of breached tickets with positive time in each state, project filter, and explicit caveats.

## Local setup / reproducibility

The original Windows analysis was run with **Python 3.13.14**, **pandas 2.3.3**, **NumPy 2.2.6**, **PostgreSQL 18**, **pgAdmin 4**, and **Power BI Desktop**. `pandas.to_datetime(..., format='mixed')` support is required; the environment passed `pip check` and 14 synthetic tests.

Place the original dataset as `archives/Help Desk Tickets.zip`. Keep the original ZIP read-only. The core Domain III script and tests are in `domain3/` and generate `domain3/local_output/`:

```powershell
cd "<your-project-directory>"
.\.venv\Scripts\python.exe .\domain3\helpdesk_domain3_measurement.py '.\archives\Help Desk Tickets.zip' '.\domain3\local_output'
.\.venv\Scripts\python.exe -m unittest discover -s .\domain3 -p 'test_domain3_measurement.py' -v
```

Use PostgreSQL database `helpdesk_analytics`. Load ticket-level results into `staging.ticket_outcomes` and event intervals into `staging.status_intervals` with CSV header enabled, then create:

- `analytics.vw_ticket_performance` — one row per ticket (**19,714**).
- `analytics.vw_ticket_workflow` — one row per Ticket × Status (**70,009**).

**CSV field order matters in positional imports:** the local Python export may place `has_special_done_cancelled` earlier than the staging table does. `scripts/prepare_postgres_csv.py` safely rewrites **header/column order only**, preserving the original and all row values:

```powershell
.\.venv\Scripts\python.exe .\scripts\prepare_postgres_csv.py .\domain3\local_output\ticket_outcomes_conditional.csv .\domain3\local_output\ticket_outcomes_for_postgres.csv
```

Use the prepared CSV for ticket-outcome imports where necessary. Run and retain the existing `sql/*.sql` queries (01–19) for schema, reconciliation, analysis and views. Import the two `analytics` views to Power BI via `localhost:5432` → `helpdesk_analytics` in **Import** mode, and use `ticket_id` for the active **1:many, single-direction** relationship (performance → workflow).

> A rebuild requires the original source ZIP, the actual Python scripts/tests, the saved SQL creation/import steps, and the PBIX. This README does not claim a fully automated one-command deployment.

## Validation and remaining assumptions

- All five ticket-outcome classifications reconcile to **19,714**; SQL independently aggregates the stored classifications to **44.1826%**.
- **81,931** positive status intervals belong to **19,711** tickets; **3** tickets have no positive intervals. SQL verified **0** ticket-level A/B interval-total mismatches and **0** invalid counted pause intervals.
- **109** tickets lack a definitive, evaluable outcome (**40 censored, 62 semantic, 7 data-quality**). Do not silently include them as nonbreaches.
- `issue_resolution_date` is missing for **254** in-scope tickets; missingness alone is not evidence of incorrect data or an unclosed issue. Outlying `resolved` → `closed` durations and nonstandard status transitions need operational review.
- **Business-rule provenance:** The 72-hour target was communicated by a professor acting in a **simulated Operations Manager role** for this academic portfolio. **Proxy stakeholder** means a person standing in for the business decision-maker during project framing; it is **not** a company representative's approval. The specific closure-based clock (Rule B), `waiting` pause, reopening treatment, `done`/`cancelled` handling, and provisional `pending_customer_approval` pause have **not** been confirmed as official company rules.
- No verified extraction time, causal evaluation, corporate sponsor approval, contractual SLA, realized ROI, or production deployment is evidenced.

## Terminology and naming

See [`docs/Terminology_and_File_Guide.md`](docs/Terminology_and_File_Guide.md) for plain-English definitions of technical terms, stakeholder-role distinctions, and which file names can safely change without breaking imports or scripts. **Internal Python/SQL column names are intentionally left unchanged for reproducibility.**

## Suggested repository structure

```text
HelpDesk-Analytics/
├── README.md
├── archives/                       # original source (check redistribution rights)
├── domain3/                        # validated Python scripts, tests and local outputs
├── sql/                            # saved 01–19 SQL queries
├── scripts/
│   └── prepare_postgres_csv.py
├── docs/
│   └── Findings_and_Recommendations.md
└── HelpDesk_Operations_Analytics.pbix
```

**Before publishing:** Review dataset redistribution rights and remove credentials, local connection secrets, `.venv/`, caches, and unnecessary large files. Screenshots can be added later. Publish only content you are permitted to share.
