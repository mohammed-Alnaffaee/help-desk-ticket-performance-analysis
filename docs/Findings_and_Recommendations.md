# Help Desk Ticket Performance — Findings and Recommendations

**Analysis scope:** Historical external-project issues of type `Ticket`, `Service`, or `HD Service`, created in 2019–2022.  
**Decision context:** Help an Operations Manager identify where to investigate tickets that **ever exceed 72 counted calendar hours before closure**. The management perspective is simulated for this academic case study, not provided by the source company.  
**Evidence status:** Descriptive and diagnostic analysis of an archived dataset. No verified company approval, intervention, operational outcome, or contractual SLA.

## 1. Measurement and population

| Item | Verified or documented value |
|---|---:|
| In-scope tickets | 19,714 |
| Confirmed breaches (working rule B) | 8,662 |
| Observed closures without breach | 10,943 |
| Evaluable tickets | 19,605 |
| Censored, semantic, or data-quality indeterminate | 109 |
| **Conditional 72-hour breach rate** | **44.1826%** |

**Working metric:** `8,662 / (8,662 + 10,943) = 44.1826%`. A breach means **more than** 72 accumulated counted hours at any observed point while not closed; a later closure does not erase the breach. The **closure-based clock (Rule B)** continues counting through `resolved` until `closed`, excludes `waiting`, and provisionally excludes `pending_customer_approval`. Time accrued before reopening remains counted. Rule **A** (stop at `resolved`) is a sensitivity comparison, not the chosen metric.

The 109 excluded outcomes are **40 censored**, **62 semantically indeterminate**, and **7 data-quality indeterminate**. These tickets are *not* assumed compliant. There is no verified formal extraction timestamp. The rate describes the **evaluable historical subset**, not an official company SLA or current operations.

## 2. Decision-relevant findings

### F1 — Historical breach prevalence is material

A total of **8,662 evaluable tickets** demonstrably exceeded the working 72-hour target. This warrants examination of workflow patterns, not a claim that employees worked continuously for 72 hours or that a contract was breached.

### F2 — The apparent 2022 improvement is not explained solely by ticket-type mix

| Creation year | Conditional breach rate |
|---|---:|
| 2019 | 43.12% |
| 2020 | 47.99% |
| 2021 | 47.74% |
| 2022 | 39.18% |

When **2022 within-type rates** are reweighted to the **2021 evaluable ticket-type mix**, the adjusted rate is **39.88%**, still below 2021's **47.74%**. The change cannot be accounted for by type mix alone. This is not causal proof of operational improvement; exclusions are larger in 2022 (88 versus 19 in 2021), and project mix or other conditions may differ.

### F3 — Rate and breach volume imply different priorities

| Ticket type | Confirmed breaches | Conditional breach rate |
|---|---:|---:|
| HD Service | 801 | 58.64% |
| Service | 1,254 | 50.34% |
| Ticket | 6,607 | 41.95% |

`HD Service` has the highest conditional *rate*, whereas `Ticket` contributes the largest *number* of breaches. Prioritization should consider both rate and count rather than ranking groups by percentage alone.

### F4 — Some projects have both substantial volume and persistently high rates

| Project (anonymized ID) | Confirmed breaches | Evaluable tickets | Conditional rate |
|---|---:|---:|---:|
| `C06hg2xcu` | 445 | 1,099 | 40.49% |
| `C06hgfz_x` | 333 | 434 | 76.73% |
| `C06hqzcz0` | 170 | 200 | 85.00% |

The last two projects also have high breach rates **within ordinary `Ticket` issues** (79.22% and 87.88%, respectively). Their high overall rates therefore cannot be explained by issue-type composition alone. Project identifiers have no verified operational interpretation; an internal review would be needed to establish context.

### F5 — Workflow durations identify investigation points, not root causes

Among **confirmed-breached tickets that accumulated positive time in the named status**:

| Status | Affected breached tickets | Median counted hours in status |
|---|---:|---:|
| `pending_deployment` | 973 | 414.16 |
| `validation` | 1,659 | 290.42 |
| `in_progress` | 7,866 | 93.64 |
| `resolved` | 6,493 | 0.05 |

The high `pending_deployment` and `validation` medians make them candidates for workflow review. The median within `resolved` is very small overall, despite very large values in some specific projects. For example, project `C06hqzcz0` has a `resolved` median of **1,131.10 hours** across **136 breached tickets** with positive time in that status. Investigating long resolved-to-closed intervals is essential before interpreting rule B as reflecting actual service-delivery delay.

**Interpretation limits:** State residence time is *not* employee labor time, and the status-level findings condition on tickets already known to have breached. One ticket can appear in multiple status groups, so the affected-ticket counts must **not** be added together to derive total tickets.

### F6 — Closure semantics materially change project comparisons

On the same B-evaluable ticket groups, the observed counts of cases breached under **closure-based Rule B** but not **resolution-based Rule A** were **189** (`C06hg2xcu`), **43** (`C06hgfz_x`), and **38** (`C06hqzcz0`). Therefore, conclusions about where the problem lies are sensitive to whether counted time continues after `resolved`. B is an *explicit working rule*, not a company-approved policy.

## 3. Proposed decisions and follow-up actions

| Priority | Proposed action | Evidence and intended decision |
|---|---|---|
| 1 | **Seek business-rule review from the academic proxy stakeholder**: `closed` versus `resolved`, reopening and cumulative hours, `waiting`, provisional `pending_customer_approval`, and treatment of `done` / `cancelled` | Prevent the report from being mistaken for a contractual or officially approved SLA calculation |
| 2 | Review high-rate, meaningful-volume projects `C06hgfz_x` and `C06hqzcz0`, stratifying by type and year | Target investigation without asserting a cause or blaming teams |
| 3 | Audit the transition and handoff process around `validation` and `pending_deployment` | Identify whether long residence times reflect approvals, deployment schedules, system behavior, or other mechanisms |
| 4 | Sample unusually long `resolved` → `closed` intervals and reconcile missing resolution dates against actual status events | Determine whether closure administration inflates the working metric B |
| 5 | Pair any 72-hour target with closure quality and waiting-state monitoring | Avoid unintended incentives for premature closure or unjustified pausing; **no such behavior is proven** in these data |

These are **investigation recommendations**, not implemented interventions or measured impact.

## 4. Quality evidence and limitations

- **Python:** event-based interval reconstruction with mixed timestamp parsing; 14 synthetic unit tests passed in the local run.
- **PostgreSQL:** 19,714 ticket outcomes reconciled; 81,931 positive status intervals, covering 19,711 ticket IDs (three tickets have no positive intervals); 70,009 aggregated Ticket × Status rows. No negative-duration violations, no inappropriate counted pause intervals, and **zero A/B ticket-level time reconciliation mismatches** in the local SQL checks.
- **Exceptional cases:** 254 missing source resolution dates are not automatically errors; seven reconciliation exceptions were withheld; 57 confirmed breaches also carry semantic flags because the breach was already proven before a later ambiguity.
- **Censoring:** the 109 withheld cases are excluded from the conditional denominator, not counted as successes. A logical whole-population classification bound from the v0.3 documentation is approximately **43.9383%–44.4912%**; it is *not* a statistical confidence interval.
- **No formal extraction date:** the hypothetical 2023-03-14 endpoint used in sensitivity testing must never be presented as an observed cutoff or an actual breach count.
- **Historical, observational data only:** findings cannot be generalized to current company performance or causal improvement; no customer satisfaction score, actual operational validation, or financial return was established. `sample_utterances.csv` contains sampled reporter messages but is not a representative satisfaction survey.

**Portfolio presentation rule:** Label the dashboard figure **“Conditional 72-Hour Breach Rate (working rule B)”**, visibly show the excluded-ticket count, and state that the target is **not a verified contractual SLA**.
