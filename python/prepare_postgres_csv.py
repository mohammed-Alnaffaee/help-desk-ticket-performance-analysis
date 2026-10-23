"""Reorder generated ticket outcome CSV columns to match PostgreSQL staging.

No source modifications, computations, rounding, or row deletions. Python stdlib only.
Usage: python prepare_postgres_csv.py <source.csv> <output.csv>
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

TARGET = [
    "ticket_id", "created_utc", "source_ended_utc", "source_resolution_utc",
    "source_final_status", "last_observed_status", "last_observed_status_time_utc",
    "observed_status_events", "observed_closed_entries", "observed_reopen_entries",
    "b_observed_counted_hours", "a_observed_counted_hours", "b_minus_a_observed_hours",
    "b_first_72h_boundary_utc", "a_first_72h_boundary_utc",
    "b_observed_threshold_exceeded", "a_observed_threshold_exceeded", "b_confirmed_class",
    "has_observed_closure_for_last_episode", "has_valid_events_after_ended",
    "has_abnormal_exit_from_closed", "has_semantic_uncertainty",
    "stage_reconciliation_error_gt60s", "source_final_disagrees_with_last_observed_status",
    "resolution_date_missing", "hypothetical_2023_03_14_235959_utc_extra_hours",
    "hypothetical_b_counted_hours", "hypothetical_b_threshold_exceeded",
    "quality_disposition", "qa_flags", "issue_type", "issue_priority", "issue_proj",
    "creation_year", "has_special_done_cancelled",
]


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python prepare_postgres_csv.py SOURCE_CSV OUTPUT_CSV")
    source, target = (Path(path).resolve() for path in sys.argv[1:])
    if source == target:
        raise SystemExit("Refusing to overwrite the original CSV. Choose a different output path.")
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open("r", encoding="utf-8-sig", newline="") as src:
        reader = csv.DictReader(src)
        found = reader.fieldnames or []
        lookup = {name.lower(): name for name in found}
        if len(found) != 35 or len(lookup) != 35 or set(lookup) != set(TARGET):
            raise ValueError(f"Unexpected CSV header. Expected 35 known columns; found: {found}")
        ordered = [lookup[name] for name in TARGET]
        count = 0
        with target.open("w", encoding="utf-8", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=ordered)
            writer.writeheader()
            for row in reader:
                writer.writerow(row)
                count += 1
    if count != 19714:
        target.unlink(missing_ok=True)
        raise ValueError(f"Unexpected row count: {count}; expected 19714")
    print(f"SUCCESS: {count} rows, {len(ordered)} columns")
    print(f"Prepared CSV: {target}")


if __name__ == "__main__":
    main()
