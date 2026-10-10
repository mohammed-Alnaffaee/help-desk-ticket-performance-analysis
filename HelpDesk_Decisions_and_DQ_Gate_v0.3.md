# Help Desk Analytics — Working Decision Log & Data Quality Gate

**Version:** 0.2 (2026-10-09)  
**Status:** Domain II framed; Domain III reconstructed candidate timeline with A/B duration sensitivity and QA flags. **Quality gate NOT passed; no validated baseline, SQL, Power BI, or company approval.**

## Status notation
[1] Evidence-backed or actually performed; [2] proposed/discussed, not approved or executed; [3] assumption requiring verification; [4] cannot be implemented or verified without an operating organization.

## Domain I carry-forward
- [1] Historical population: external projects (`issue_proj` length > 6, per `FEATURES.md`), types `Ticket`, `Service`, `HD Service`, created 2019–2022. **19,714 unique issues**.
- [1] Business requirement as framed for the project: a ticket should not **remain open after exceeding 72 counted calendar hours**. The professor serves as a proxy Operations Manager; do not call the target a contractual SLA.
- [2] `waiting` is a previously selected pause rule; direct provenance from the professor is not documented. `pending_customer_approval` is a **provisional pause rule that requires Proxy validation**. There are zero positive durations for `pending_customer_approval` in the chosen population.
- [2] Initial Business Case proxy review/sign-off is outstanding; [4] corporate sponsor sign-off unavailable.
- [3] Risk of unintended behavior from the 72h target (early closing, unjustified waiting, degraded resolution quality), not a factual finding.

## Domain II — Analytics problem
**Working Analytics Problem Statement [2]:** Determine, among historical external-project tickets in the defined population, which tickets **ever passed 72 counted hours while still open**, including tickets subsequently closed and tickets still unresolved at the observation cutoff. Quantify the extent and distribution of such historical events, then examine possible operational associations without claiming causation.

**Primary ticket-level outcome [2]:** `ever_breached_72h_while_open` (Boolean, with separate `indeterminate` classification where timeline cannot be reliably reconstructed). Supporting fields: `first_breach_timestamp`, `closure_status`, `observation_cutoff`, `counted_seconds`, `quality_flag` where available.

**Input/grain:** `issues.csv` is one row per ticket (`id`); `issues_change_history.csv` contains status/assignee changes by `issueid`; `issues_snapshot.csv` is per assignee turn and must not be joined naively for ticket counting; `sample_utterances.csv` is sample-only reporter/assignee communication. Candidate stratification: issue type, project, creation year, priority, workflow states, assignee changes/contributors.

**Measurement rules awaiting final approval [2]/[3]:**
1. **Working choice B [1 as a project decision, not validated as company policy]:** the counted clock stops when entering `closed`; time from `resolved` to `closed` **counts** except approved pause periods. Resume on `reopened`; nonstandard direct exits from closed require review. **A (`resolved` stops the clock) is comparison-only.** Do not reverse A and B. `done`/`cancelled` are special states still awaiting policy validation.
2. Define interval reconstruction from `issue_created` + sorted history status changes; pause only in approved statuses, never count intervals after closure as open.
3. Determine whether to extend a last observed active status to the observation cutoff; `2023-03-14 14:19:32 UTC` is merely the **latest observed event**, not a proven extract timestamp.
4. Separate `breached_before_cutoff`, `closed_without_breach`, `still_open_not_yet_breached`, and `indeterminate`. Do not classify still-open/not-yet-breached as conclusively compliant.
5. Approve breach share denominator and treatment of censored/indeterminate observations before publishing a baseline.
6. Threshold is strictly **greater than 72 counted hours**, not simply greater than 72 raw wall-clock hours.

## Domain III — Initial read-only audit [1]

| ID | Evidence from source | Consequence / provisional action | Verification gate |
| --- | --- | --- | --- |
| DQ-01 | Mixed timestamp representations. Parsing `issue_created` using `format='mixed'`, UTC, yields all 66,691 issue timestamps and population 19,714. | Preserve original strings and use an explicit mixed-format parse; do not use previously incorrect 9,764 population. | Recheck scoped year totals: 2019=4,318; 2020=4,384; 2021=4,975; 2022=6,037. |
| DQ-02 | 254 missing `issue_resolution_date`, **108** of which have final `issue_status='closed'`; 146 have other statuses. | Do not drop all 254 and do not treat all as currently open. Reconstruct closure timing using status history where defensible. | Audit cases and reconcile closure/other status timestamps before classifying outcomes. |
| DQ-03 | Workflow-event reconstruction vs supplied `wf_*` has **7 tickets** with >60 seconds of deviation, IDs 38192, 42149, 1002268, 1002220, 1002867, 1002199, 1002442. | Flag for targeted investigation; do not hide mismatches or silently overwrite values. | Resolve or flag as indeterminate if they can affect the threshold. |
| DQ-04 | 777 tickets have positive `wf_closed` durations; 243 have **over 72 hours solely in `wf_closed`**. | `wf_total_time - wf_waiting` cannot safely be used as an open-ticket duration measure. | Rebuild status intervals; verify intervals in `closed` do not increase an open-ticket clock. |
| DQ-05 | 11,926 tickets have positive `wf_waiting`; zero scoped tickets have positive `wf_pending_customer_approval`. | A pause is materially relevant for waiting. Preserve pending approval as provisional but it does not affect this population's precomputed state-time aggregates. | Reconcile excluded intervals and obtain Proxy confirmation for pending approval. |
| DQ-06 | Three scoped tickets have no status changes recorded up to `ended` (one may still have other history). | May be legitimately unchanged-state tickets, not necessarily errors. | Compare inferred starting status `open` with aggregated workflow durations for these cases. |
| DQ-07 | Last observed event: `2023-03-14 14:19:32 UTC`; no formal extract-time guarantee. | Choose/label cutoff clearly; avoid presenting historical observations as current 2026 performance. | Validate that extension of open-state time from last change to cutoff is justified; sensitivity analysis if needed. |

**Checks passed [1]:** 19,714 unique IDs (no duplicates in scope); no resolution-before-created dates in scope; all 19,714 `wf_total_time` values reconcile to the sum of included `wf_*` stage durations to 1 second; scope reporter utterances = 5,517 (5,700 in full sample). These are structural checks, **not** proof that the 72h calculation is correct.

## Execution sequence and evidence gate
1. **Executed [1]:** working B decision, reconstructed testable ticket-state timeline and A comparison; all 19,714 issues included in ticket-level comparison, candidate intervals cover all positive durations; 9 synthetic tests passed. Source `ended` is only a reconstruction bound, NOT an approved observation cutoff. Remaining decisions: terminal/special states, reopening/direct exits, cutoff and pause rules.
2. [2] Domain III: write reproducible Cleaning & Transformation specification and issue disposition; validate timeline/reconciliation on both normal and exception examples.
3. [2] Domain IV: justify descriptive/diagnostic methods and SQL/Statistics/Power BI only when they serve defined questions.
4. [2] Domain V: only after the quality gate, compute a defensible baseline and segment patterns; distinguish association from root-cause claims.
5. [2] Portfolio deliverables: relational model, SQL queries, business KPI specification, Power BI report, QA report, insights/recommendations, README, limitations and decision log.
6. [4] Domain VI/VII: no claims of production deployment or ongoing production monitoring; optional documented adoption/refresh plan only.

**Current stop/go decision:** Quality gate is **NOT PASSED**. Baseline and dashboard are intentionally not presented as verified outputs.


## 2026-10-09 continuation — Status Timeline v2 and A/B policy sensitivity [1 execution]

**Corrected policy wording (authoritative for the working project):**
- **B — working choice:** start at ticket creation; count all non-paused, non-`closed` states including `resolved` and any time **between `resolved` and `closed`**; pause in `waiting` and (provisionally) `pending_customer_approval`; stop while in `closed`. If later `reopened`, resume cumulatively rather than erasing already counted time. Direct departures from `closed` into other states are flagged because their meaning is not validated.
- **A — sensitivity comparator ONLY:** stop at entering `resolved`, and resume at `reopened` or departure from `closed` (to make episodes comparable). This A rule still needs interpretation when statuses change to active-looking states after resolved without an explicit reopen; those are flagged.
- No baseline, official breach flags/rate, or exposure denominator calculated. No published SLA claim.

**QA results (source ended bound, not confirmed extract date):**
- [1] 19,714 unique tickets checked; interval coverage matches `created_at` to `ended` for every ticket. 3 have zero elapsed time and appear in ticket-level output but have no positive-length interval row. 81,865 positive intervals.
- [1] 118 status events for 111 tickets occur after the per-ticket `ended` value and were **not silently included** in truncated intervals; 2 final status discrepancies; 7 >60-second workflow-reconciliation anomalies.
- [1] 50 tickets move out of `closed` without a `reopened` label; 69 have some `done`/`cancelled` interval; 146 are not finally `closed` in the source. Overlap exists; 364 tickets carry at least one B-review holdout marker. `closed` with missing `issue_resolution_date` (108 cases) is an independent audit warning, not automatic evidence of open status.
- [1] Comparison-only A/B difference before QA-gate: 14,627 tickets have B longer than A; summed candidate difference is about 2,046,671 counted hours, affected-ticket median ~1.27 minutes (long-tailed). A has 1,160 tickets with active-looking changes after resolved without explicit reopen, so the A comparator has additional uncertainty. **These are exposure-duration sensitivity diagnostics, not approved performance results.**

**Deliverables:** `helpdesk_domain3_timeline_v2.py`, `test_helpdesk_domain3_timeline_v2.py`, `helpdesk_domain3_qa/ticket_status_intervals_B_vs_A_v2.csv`, `helpdesk_domain3_qa/ticket_clock_comparison_A_vs_B_v2.csv`, `helpdesk_domain3_qa/timeline_B_vs_A_validation_v2.json`, plus preexisting targeted QA CSVs. Source ZIP remains unchanged.

**Open before Baseline (Gate = NOT PASSED):** proxy confirm provisional pause; decide how nonstandard terminal/special states count (`done`, `cancelled`, exits from `closed` without `reopened`); establish defensible observation cutoff for non-closed tickets; decide cumulative vs episode-reset policy; disposition of reconciliation anomalies, and denominator/censoring approach.

---
## 2026-10-09 — Version 0.3 appendendum (supersedes v0.2 `ended`-bound candidate for measurement)
- **[1] Working B applied correctly:** `resolved`→`closed` duration counts (except approved Pause), `closed` excludes duration, reopening accrual is cumulative. A remains comparator only.
- **[1] Domain III event evidence:** 82,004 scoped status events, **118** post-`ended` events retained across **111** tickets. `ended` is NOT a cutoff; for the primary metric we observe intervals only until the next known status event. Missing official extraction timestamp is explicitly acknowledged.
- **[1] Quality/triage:** 7 source-stage discrepancies excluded as data-quality indeterminate (including 2 final-status mismatches). `done`/`cancelled` and nonstandard exits from closed receive semantic holdout if they could affect classification. Missing 254 resolution dates do not imply 254 errors. Censored unresolved is not counted as success.
- **[1, conditional] Observed-event analysis:** `confirmed_breached=8,662`, `closed_without_breach=10,943`, `censored_or_indeterminate=109`, `evaluable_denominator=19,605`; conditional ratio **44.1826%**. This is NOT official SLA baseline or verified organizational performance.
- **[3] Hypothetical sensitivity:** 2023-03-14 23:59:59 UTC adds 32 *unverified* threshold flags if final nonclosed states are assumed unchanged. Do not append them to the confirmed numerator.
- **[1] B/A sensitivity:** B minus A duration = approximately **2,047,293 observed counted hours** across tickets, affected median 1.27 minutes; the large upper tail reflects lengthy `resolved`/`pending_deployment`→`closed` gaps (e.g. IDs 39485, 39277, 39857). Never interpret this sum as wasted labor.
- **[1] Domain IV method decision documented:** Descriptive/Diagnostic, not causal modeling. **[2]** SQL/Statistics/Power BI to be implemented and verified in next stage; do not claim done.
- **Open [2]/[3]:** Proxy validation of B/reopen and `pending_customer_approval` pause; interpretation of terminal-like statuses, formal extraction timestamp unavailable. Original v0.2 findings remain audit history but its `ended`-bounded duration totals are superseded.
