# PostgreSQL reproduction guide (Windows / PostgreSQL 18)

This describes how to rebuild the **SQL staging tables and reporting views** from the original public dataset and the project's Python scripts. It does not require the previously committed derived CSV snapshots. The procedure has been documented against the code's column definitions; a fresh-database execution has **not** yet been verified by the repository maintainer.

## Prerequisites

- PostgreSQL 18 and `psql` (or pgAdmin 4 for the SQL statements).
- Python 3.13, `pandas` 2.3.x, and `numpy` 2.2.x.
- The **Help Desk Tickets** source ZIP in a local folder. The archive must contain `Help Desk Tickets/issues.csv` and `Help Desk Tickets/issues_change_history.csv`. See the README for dataset attribution. Do not put your local source ZIP or DB credentials in Git.
- Run commands from the cloned repository root. On Windows, replace `python` or `psql` with their full executable path if not on PATH.

## 1. Produce the original analysis outputs locally

From PowerShell in the repository root:

```powershell
python -m pip install pandas==2.3.3 numpy==2.2.6
python -m unittest discover -s python -p "test_*.py" -v
python python/helpdesk_domain3_measurement.py "C:\path\to\Help Desk Tickets.zip" "local_output"
python python/verify_exported_results.py "local_output"
python python/prepare_postgres_csv.py "local_output/ticket_outcomes_conditional.csv" "local_output/ticket_outcomes_postgres.csv"
```

The first CSV remains untouched. The last command produces the *same values in a different column order* to match the table definition. The pre-import checks should report **19,714 ticket rows** and **81,931 positive status intervals**. Stop if they do not.

## 2. Create an empty database and its staging schema

In pgAdmin create a database named `helpdesk_analytics`, **or** create it with:

```powershell
createdb -U postgres helpdesk_analytics
```

Then from the repository root:

```powershell
psql -U postgres -d helpdesk_analytics -v ON_ERROR_STOP=1 -f "sql/00_create_staging_tables.sql"
```

This creates `staging.ticket_outcomes` (35 columns, one row per ticket) and `staging.status_intervals` (10 columns, one row per positive observed interval), including basic integrity checks. It **does not** delete or reset existing tables. Use an empty database for a repeatable first-time import.

## 3. Import both CSV files with psql

Open an interactive `psql` session **from the repository root**, so the relative file paths resolve:

```powershell
psql -U postgres -d helpdesk_analytics
```

Run these **psql commands**, not SQL Query Tool commands. Keep the order: tickets first, intervals second because the second table references ticket IDs.

```text
\copy staging.ticket_outcomes FROM 'local_output/ticket_outcomes_postgres.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy staging.status_intervals FROM 'local_output/observed_status_intervals.csv' WITH (FORMAT csv, HEADER true, NULL '')
```

These are client-side `\copy` commands. Standard SQL `COPY` inside pgAdmin reads files from the **PostgreSQL server** instead of your desktop and often fails due to path/permission issues. If using pgAdmin's Import/Export UI instead, specify CSV, Header ON, UTF-8, matching column order, and NULL as an empty field.

If you see `duplicate key`, stop: the table already contains data. **Do not import the same file twice** or truncate tables unless you intentionally want to replace a local test database.

## 4. Verify the data *before* running analysis

Run in psql or pgAdmin:

```sql
SELECT
  COUNT(*) AS tickets,
  COUNT(*) FILTER (WHERE b_confirmed_class = 'confirmed_breached') AS breached,
  COUNT(*) FILTER (WHERE b_confirmed_class IN ('confirmed_breached','closed_without_breach')) AS evaluable
FROM staging.ticket_outcomes;

SELECT COUNT(*) AS intervals,
       COUNT(DISTINCT ticket_id) AS tickets_with_intervals
FROM staging.status_intervals;
```

Expected: `tickets=19714`, `breached=8662`, `evaluable=19605`, `intervals=81931`, `tickets_with_intervals=19711`. The other three tickets have no positive-duration intervals.

For independent checks, execute `sql/01_kpi_reconciliation.sql`, `sql/12_workflow_validation.sql`, `sql/13_time_reconciliation.sql`, and `sql/17_final_sql_quality_checks.sql`. The time reconciliation should show 3 tickets without intervals and 0 A/B mismatches at one-second tolerance.

## 5. Build both Power BI reporting views

```powershell
psql -U postgres -d helpdesk_analytics -v ON_ERROR_STOP=1 -f "sql/18_ticket_performance_view.sql"
psql -U postgres -d helpdesk_analytics -v ON_ERROR_STOP=1 -f "sql/19_ticket_workflow_view.sql"
```

Expected: `analytics.vw_ticket_performance` has 19,714 tickets; `analytics.vw_ticket_workflow` has 70,009 ticket-status groups representing 19,711 tickets. The latter does not include the three zero-duration tickets.

The remaining numbered SQL files (`02` through `17`) are supporting analyses and QA reports. They can be run from pgAdmin after the import.

## 6. Power BI Desktop

Connect to your local PostgreSQL server and the `helpdesk_analytics` database (typically `localhost:5432`). Select the `analytics.vw_ticket_performance` and `analytics.vw_ticket_workflow` views. Alternatively, open the existing PBIX and use **Data source settings** to point to your own PostgreSQL instance, then refresh. Your local username/password must stay outside GitHub.

**Privacy:** The repository's pre-existing PBIX may contain an imported row-level data model. Do not redistribute it without completing the privacy review documented in `docs/Privacy_Review.md`.

## Limitations

The pipeline uses an academic **working** 72-hour clock definition, not a source-company contractual SLA. Saved results represent a historical 2019–2022 subset. This guide supplies the missing schema/import procedure but is not evidence of a new, independent full-run verification.
