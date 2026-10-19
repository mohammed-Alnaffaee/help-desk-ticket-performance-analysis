# Analysis methodology and decisions

## Analytical objective

Identify **which historical ticket types, years, anonymized project groups and workflow statuses** warrant operational investigation under a project-defined **72 counted-hour target**.

**Selected approach: Descriptive and diagnostic analytics.** This is observational work: it measures patterns and describes potential investigation points; it does not establish causes, predict future outcomes, or quantify intervention impact.

## Why these methods and tools?

- **Python** reconstructs status-event time intervals, handles mixed timestamp formats, classifies censoring/ambiguity, and provides unit tests. This transformation needs event-sequence logic.
- **PostgreSQL / SQL** performs population reconciliation, rate segmentation, status aggregation, project comparisons, and independent data-quality checks.
- **Statistics** supports skewed-duration summaries (median), uneven denominator interpretation and simple ticket-type standardization. It is not a causal model or a confidence interval.
- **Power BI** presents the decision-level KPI, yearly/type/project breakdowns and operational status patterns.

## Status of implementation (October 2026)

| Stage | Status |
|---|---|
| Python timeline reconstruction and conditional classification | Implemented and locally validated |
| Python unit tests / exported-result checks | 14 and 16 checks, respectively, reported as passing locally |
| SQL analysis | 19 files saved and local reconciliations completed |
| SQL reporting views | `analytics.vw_ticket_performance`, `analytics.vw_ticket_workflow` implemented |
| Power BI Desktop | Two dashboard pages created |
| PostgreSQL staging DDL/import commands in GitHub | Not yet published; reproducibility gap |
| Source-company policy approval or operational deployment | Not obtained |
| Dashboard PNG screenshots | Two historical report previews added under `docs/images/` |

## Measurement and interpretation decisions

1. **Rule B** is the working, closure-based 72-hour calculation, with explicit pause and reopening assumptions; **Rule A** (resolution-based) is a sensitivity comparator.
2. The KPI denominator includes only **confirmed breaches and observed closures without breach**. Censored/indeterminate cases are excluded, not treated as compliant.
3. Annual comparisons are descriptive; the 2021–2022 ticket-type standardization does not establish improvement or causality.
4. Median counted status hours are computed **within already-breached tickets with positive hours in that status**. They are not staff working hours, and one ticket can appear in several status categories.
5. `resolved`-to-`closed` administration may inflate Rule B residence time; business-policy confirmation is outstanding.
6. **No contractual SLA** is evidenced. The academic supervisor acted as a simulated Operations Manager, not a sponsor from the source company.

## Remaining work before final portfolio release

- Verify rights to redistribute already-published derived exports and the imported data model in the PBIX.
- Add staging-table definitions and import procedure to enable independent SQL reproduction.
- Review the branch changes and merge only after approval.

For detailed scope, exclusions, QA and exact results, see [Cleaning and Transformation Rules](Cleaning_and_Transformation_Rules.md) and [Findings and Recommendations](Findings_and_Recommendations.md).
