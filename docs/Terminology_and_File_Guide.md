# Terminology and File Naming Guide

This page clarifies terms used in the Help Desk Ticket Performance Analysis project. Use the short explanations in interviews; keep technical field names in code consistent with the validated data model.

## Project and analysis terms

| Term | Plain-English meaning in this project |
|---|---|
| **Operational target (72 hours)** | A project-defined threshold. The ticket must not remain open beyond 72 counted calendar hours. It is **not** a verified contractual SLA. |
| **Closure-based clock (Rule B)** | The selected **working rule**: time keeps accumulating through `resolved` and stops upon entering `closed`; approved pause periods do not count. Reopening may resume accumulation. Not company-validated. |
| **Resolution-based clock (Rule A)** | A comparison rule that stops at `resolved`. Used for sensitivity analysis only, not the dashboard's principal rule. |
| **Conditional breach rate** | Confirmed exceeded tickets divided by classifiable tickets, under the working rule: **8,662 / 19,605 = 44.18%**. It excludes 109 tickets with unconfirmed outcomes. |
| **Evaluable tickets** | Tickets that can be classified as either a confirmed breach or an observed closure without breach. |
| **Censored** | A ticket whose future outcome cannot be confirmed from the available observation history. Being unconfirmed is not proof of compliance. |
| **Indeterminate** | A ticket whose classification remains unclear due to status meaning or data quality. |
| **Status timeline / workflow history** | The ordered sequence of ticket status changes used to calculate counted time. |
| **Status interval** | One observed period between two recorded status events. |
| **Grain** | What one row represents: one ticket in the performance table; one Ticket × Status in the workflow view. |
| **Staging** | Database tables used to load and validate prepared outputs before exposing them through reporting views. |
| **Reconciliation** | Checking that SQL counts and accumulated durations agree with the previously tested Python outputs. |
| **Median / P90** | The midpoint of a distribution / the value at or below which about 90% of observations fall. They help describe skewed durations. |
| **Proxy stakeholder** | In this academic project, the professor acted as a stand-in for a possible Operations Manager, supplying the **72-hour objective**. This is not a source-company manager or formal sponsor approval. |
| **Descriptive / Diagnostic analytics** | Measuring what happened / examining where differences or patterns may warrant investigation. Neither proves a cause. |

**About “Tometry”:** That exact word was **not found** in the reviewed README, findings report, or CSV-preparation script. If it appears elsewhere, check the original spelling before renaming or defining it.

## Professional file naming: what to keep now

| Current path | Recommendation | Reason |
|---|---|---|
| `README.md` | **Keep** | Standard entry point in a GitHub repository. |
| `HelpDesk_Operations_Analytics.pbix` | **Keep** (optional name `HelpDesk_Ticket_Performance.pbix` before publishing) | Current filename is professional and already works; don't risk confusion by renaming mid-project. |
| `sql/01_...sql` to `sql/19_...sql` | **Keep** | Numbered, descriptive, reproducible analysis sequence. |
| `scripts/prepare_postgres_csv.py` | **Keep** | Precisely states that the script prepares the CSV for PostgreSQL; update the README if ever renamed. |
| `domain3/` | **Keep on the working Windows machine**; optional `data_preparation/` for a later public copy | Renaming now would invalidate local commands and paths. |
| `domain3/local_output/*.csv` | **Keep locally** | Generated, tested analytical exports. Don't publish large outputs without checking dataset license. |
| `archives/Help Desk Tickets.zip` | **Keep original name** | Preserve the source archive unchanged. Verify redistribution permissions before publishing. |
| `docs/Findings_and_Recommendations.md` | **Keep** | Clear, conventional analysis-report filename. |

## What should not be renamed manually

- Database schemas and views: `staging.ticket_outcomes`, `staging.status_intervals`, `analytics.vw_ticket_performance`, and `analytics.vw_ticket_workflow`.
- Columns and DAX dependencies: `ticket_id`, `b_confirmed_class`, `b_counted_hours`, `evaluable_flag`, `breached_flag`, and related columns.
- Python script/function/test names while the pipeline is in use: they may be referenced by commands, imports, tests, or documentation.

## How to describe the academic stakeholder professionally

Use this wording **once under methodology or assumptions**, not in every section:

> The 72-hour operational target was supplied during academic supervision, with the professor acting as a simulated Operations Manager. The measurement rules were developed for portfolio analysis and have not been formally validated by the source organization.

In the business summary and charts, refer simply to the **Operations Manager decision context**. This preserves the truth without making the project sound like a real client engagement.
