# Domain IV — Methodology Selection (initial documented decision)

## Decision and justification

**[1] Methodological choice:** **Descriptive + Diagnostic Analytics**, explicitly non-causal. The required outcome is historical *ever exceeded >72 counted hours while not closed*, and the business decision is **where to investigate or improve the help-desk workflow**. No forecast, intervention effect or ML predictor is required to answer this question.

**[1] Data preparation:** an auditable event-based transformation with explicit censoring/indeterminate labels and comparison A/B. Python was used because reproducing and testing a mixed-format, time-ordered event clock was a necessary validation task; do not introduce an ML model.

**[2] Next delivery tools:** SQL for independently verifiable scope, relational joins, aggregate KPI segments and decision-relevant checks; basic Statistics for skew, quantiles, uneven denominators and uncertainty (not causal proof); Power BI for a decision-focused dashboard. These tool choices are **justified for the workflow but not yet executed**. Do not claim SQL or Power BI completed.

## Build order

1. Confirm scope and import `ticket_outcomes_conditional.csv` / `observed_status_intervals.csv` into SQL staging alongside source metadata, preserving ticket grain and quality flags. Reconcile SQL conditional numerator **8,662**, denominator **19,605**, unresolved **109**.
2. Use SQL to compare by creation year, ticket type, project and priority; suppress/flag tiny groups, and separately profile `resolved`→`closed` lag. No naive `issues_snapshot` one-to-many join.
3. Validate distributions, trends and unusual high outliers before interpreting them. Distinguish state duration from staffing productivity and correlation from causes.
4. Create Power BI dashboard with conditional target measure, count and proportion censored, year/type/project slices, footnotes on B policy and cutoff sensitivity; link findings to a specific *potential* management decision.
5. Document reproducible run command, cleaning/rules, tests, limitations and portfolio README. No organizational implementation/ROI claim.

**Proxy validation needed [2]:** final business policies and Business Case review. **Deployment [4]:** corporate deployment cannot be verified from this historical public-style archive.
