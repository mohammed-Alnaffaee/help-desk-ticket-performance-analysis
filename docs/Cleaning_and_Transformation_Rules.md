# Domain III — Cleaning & Transformation Rules / Dispositions

**Version:** 0.3 · **Source:** unchanged `Help Desk Tickets.zip` · **Scope:** 19,714 issues · **UTC**

## Measurement policy and evidence

- **B — selected working policy (not company-validated):** The clock runs while the ticket has not entered `closed`, including `resolved`, `resolved_under_monitoring`, and `pending_deployment`. It pauses during `waiting`; `pending_customer_approval` is a **provisional** pause requiring Proxy confirmation. It stops while in `closed`. Accumulated time is retained and resumes following an explicit `reopened` event. Direct exits from `closed` without `reopened` are measured provisionally but flagged for semantic review.
- **A — comparison only:** Clock stops upon `resolved` and resumes on explicit reactivation; not the business KPI.
- **Threshold:** strict `>72 × 3,600` *counted* seconds. The condition is **ever exceeded while open**. Subsequent closure does not erase a breach.
- **Source `ended` is not a verified extraction timestamp:** interval reconstruction uses the observed `status` event at the next timestamp. The period following the final observed event is **not added** to the primary metric unless there is a subsequently observed transition. All valid status changes **after** `ended` are included.
- **Last status observation for non-closed tickets:** if already >72 at an observed event, confirmed breached; otherwise label `censored_no_proven_breach`, never compliant. Terminal-looking `done` or `cancelled` and nonstandard exits from `closed` are not silently treated as approved terminal or reopening semantics.
- **Cumulative-clock assumption [3]:** time accrued in prior open episodes remains when reopened. Initial state from `issue_created` is assumed `open` until first status event. These are source-driven working assumptions, **not formal company policy**.

## Transformations and tests

| Rule | Action | Verification/disposition |
|---|---|---|
| DQ-01 | Preserve original ZIP; parse mixed time strings (`format='mixed'`, `utc=True`); filter external `issue_proj` code length >6 and three types, creation years 2019–2022 | Assert 19,714 unique issue IDs, year totals preserved; no source rows edited |
| DQ-02 | Use `issues.csv` at ticket grain and `issues_change_history.csv` at status-event grain; sort `(issueid, event_time, event_id)` | Prevent fanout from `issues_snapshot.csv`; no negative intervals; all 82,004 scoped events reconstructed |
| DQ-03 | Include 118 valid transitions after `ended`, touching 111 issues | Preserve observed closure evidence; mark after-`ended` as diagnostic, **not automatic exclusion** |
| DQ-04 | Never replace observed closure events with missing `issue_resolution_date`; missing date alone not cause for exclusion | 254 missing resolution dates, of which 108 source statuses `closed`; outcomes remain event-based |
| DQ-05 | Reconcile status intervals (bounded at `ended` **for audit only**) to `wf_*` aggregates | 7 tickets with >60s disagreements explicitly excluded as `indeterminate_data_quality` (including the two final-status mismatches) |
| DQ-06 | Exclude durations with state `closed` and `waiting` from B; provisionally also `pending_customer_approval` | Synthetic tests; pause in `waiting` does not count; zero positive pending-approval state duration in original scope |
| DQ-07 | Distinguish `closed`, `resolved`, `reopened`, `done`, `cancelled` and implicit departures | `done`/`cancelled` and implicit exits: if breach already occurred *before* first ambiguous event, retain confirmed breach; otherwise exclude as `indeterminate_semantic` |
| DQ-08 | Check last event state against `issue_status` | Two mismatches are among the seven DQ exclusions; never create an unseen `closed` event from final status alone |
| DQ-09 | Compute B and comparison A; test `B >= A` per ticket; do not interpret elapsed clock hours as employee working hours | 14 synthetic unit tests + structural/reconciliation assertions |
| DQ-10 | Do not infer additional nonclosed time from `ended`, `last_change_date`, or March 14 for the primary KPI | Run separate **hypothetical sensitivity** extending the last observed non-closed state to `2023-03-14 23:59:59 UTC` only |

## Outcomes and quality gate

Ticket-level classes are mutually exclusive:

- `confirmed_breached`: status-event evidence proves >72 counted hours before any relevant ambiguity.
- `closed_without_breach`: fully observed final entry into `closed`, <=72 counted hours, and no unresolved serious ambiguity.
- `censored_no_proven_breach`: last observed state was not closed; no established breach by last observed status event.
- `indeterminate_semantic`: ambiguous terminal/reopen path changes interpretability and a breach has not been proven before it.
- `indeterminate_data_quality`: 7 source/timeline reconciliation exceptions, withheld regardless of tentative threshold result.

**Conditional analytic metric** = `confirmed_breached / (confirmed_breached + closed_without_breach)` = **8,662 / 19,605 = 44.1826%**. This describes the **evaluable subset** under B working assumptions, **not** a contractual SLA result, not the entire-census official breach percentage, and not the company's current performance.

Of 19,714 scoped tickets, 109 remain **censored/indeterminate**. An honest whole-population interval, if all exclusions could be either outcome, is **43.9383% to 44.4912%**; this is a logical data-classification bound, not a statistical confidence interval. Do **not** count censored as successful.

**Hypothetical cutoff sensitivity:** Extending last observed nonclosed status to March 14, 2023, 23:59:59 UTC adds **32** threshold flags (31 previously censored and 1 semantically uncertain) before QA exclusions. **This is NOT an extraction date, and these 32 are NOT confirmed historical breaches.**

## Remaining validation [2]/[3] and recommendations

1. Obtain Proxy confirmation that the exact `closed` rule B and cumulative reopening rule match the intended business interpretation; confirm whether `pending_customer_approval` is paused. No evidence of contractual SLA.
2. Review 7 inconsistent tickets and 62 semantic indeterminates if a company-standard, fully auditable numerator/denominator is required. Study `done`/`cancelled` and closed-to-nonreopened transitions, not just final labels. Do not invent timestamps or close cases from missing data.
3. Validate what large periods in `resolved`/`pending_deployment` represent before recommending labor, staffing or productivity measures. No claims of causal impact, customer dissatisfaction or money saved.
4. Dataset contains 2019–2022 ticket creations; never infer 2026 operations. Full production deployment and corporate approval unavailable [4].

**Quality status:** Conditional evidence/metric ready for documented exploratory and portfolio analysis; **corporate KPI sign-off and full-exception resolution are outstanding.**
