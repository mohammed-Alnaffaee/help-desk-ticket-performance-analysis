# Public artifact privacy review (24 October 2026)

**Scope:** `data/derived/*.csv`, their source/export schemas, Power BI screenshots, and `powerbi/HelpDesk_Operations_Analytics.pbix` in this repository's current public branch. This is a publication-risk check for an educational portfolio, **not** a legal compliance certification or source-organization clearance.

## What is known

1. The Python exporter for `ticket_outcomes_conditional.csv` creates **35 structured fields**: ticket IDs, precise event timestamps, statuses, measured hours, outcome classes, QA flags, ticket type/priority, and anonymized project codes. The `observed_status_intervals.csv` exporter creates **10 structured fields**: ticket ID, timestamps, status, durations and pause/count flags. Reporter-message samples are **not** inputs to the analytical results.
2. The published derived files are **row-level records**, not only aggregates. `ticket_id` plus precise timestamps and project codes may be linkable to other data even if names and contact details are absent.
3. The published dashboard screenshots were visually checked: they display aggregated charts, coded project labels and overall counts, without obvious names, emails or phone numbers. That is a visual check only.
4. The Power BI `.pbix` contains an imported data model, according to the project documentation. The embedded model may contain individual ticket rows, while report screenshots show aggregates. The `DataModel` binary is **not** decoded by the repository scanner.

## Automated scan

Run from repository root:

```powershell
python scripts/privacy_audit.py --strict --output local_output/privacy_audit.json
```

GitHub Actions also runs the same read-only scan on changes to the scanner/workflow and derived artifacts: [Public artifact privacy screen](../.github/workflows/privacy-audit.yml). The script reviews **all rows** of tracked derived CSVs for sensitive column names, email-like values, Saudi phone-number patterns and possible secret assignments; it also inspects the **readable** parts of the PBIX ZIP container. Reports contain **counts only, not matching values**.

A passing automated scan means only that *those pattern checks* did not flag direct identifiers. It does **not** mean the CSVs or embedded Power BI data are approved for publication, and it cannot detect every form of confidential or reidentifiable data.

## Manual PBIX review still necessary

Before publicly redistributing an updated Power BI file, open it **locally** in Power BI Desktop and verify:

- **Power Query / Transform data:** remove unneeded text, comments, message bodies, personal contact fields and raw data not needed for the dashboard; inspect **all loaded queries**, including hidden ones.
- **Model view / Data view:** inspect table schemas and representative row-level records, not only visual screenshots. Pay attention to exact ticket IDs, timestamps, linked categories and any natural-person fields.
- **Data source settings:** do not include local credentials, passwords or private file paths in documentation or exports. Review any data-source URL/server metadata.
- Confirm source license/attribution (Mendeley dataset version and CC BY terms) and whether redistribution of derived **individual-level** records is appropriate. If uncertain, publish just the reproducible code, documentation and aggregated dashboard screenshots, not the PBIX or row-level CSVs.

## Publication decisions and remaining risk

- **No new raw source ZIP** was added.
- The current repo already has derived CSVs and PBIX in Git history from earlier work. Moving/deleting a file in a new commit **does not erase that history**; history rewriting would require a separate, carefully planned operation.
- This review does **not** establish source-company permission, deployment, an actual SLA, or anonymization guarantees.
- Current conservative stance: share the public README, methods, SQL/Python code, and aggregate screenshots as portfolio evidence; treat full exported row-level data and the downloadable PBIX as **not cleared by this review** until the manual PBIX and linkage checks are completed.

**Status:** Programmatic checks and manual PBIX model review are separate steps. This document must be updated with the scan outcome once run; no legal/privacy clearance is implied.
