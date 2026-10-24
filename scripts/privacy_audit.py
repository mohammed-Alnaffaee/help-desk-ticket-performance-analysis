#!/usr/bin/env python3
"""Read-only, privacy-focused audit of the repository's published artifacts.

No personal values are printed or uploaded. Scans complete CSVs using the Python
standard library; inspects PBIX container entries and readable metadata, but
cannot semantically decode Power BI's compressed/binary DataModel.

Usage:
    python scripts/privacy_audit.py
    python scripts/privacy_audit.py --strict --output local_output/privacy_audit.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EMAIL_RE = re.compile(r"(?i)(?<![\w.])[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}")
SA_PHONE_RE = re.compile(r"(?<!\d)(?:\+966[\s\-]?5\d{8}|00966[\s\-]?5\d{8}|05\d{8})(?!\d)")
SECRET_RE = re.compile(
    r"(?i)\b(?:password|passwd|api[_-]?key|client[_-]?secret|access[_-]?token)"
    r"\s*[:=]\s*['\"]?[^\s,'\";]{6,}"
)
SENSITIVE_HEADER_RE = re.compile(
    r"(?i)(?:^|_)(?:email|e_mail|phone|mobile|first_name|last_name|full_name|"
    r"reporter_name|reporter_email|customer_name|employee_name|person_name|"
    r"address|contact|ip_address|comments?|messages?|narrative|"
    r"description|notes?|free_text|raw_text)(?:_|$)"
)
PBIX_READABLE_SUFFIXES = (".xml", ".json", ".txt", ".m", ".pbit")
PBIX_READABLE_NAMES = {"connections", "settings", "version", "diagramlayout"}
PBIX_READ_LIMIT = 2 * 1024 * 1024


def detect(text: str, counts: Counter) -> None:
    if EMAIL_RE.search(text):
        counts["email_values"] += 1
    if SA_PHONE_RE.search(text):
        counts["saudi_phone_values"] += 1
    if SECRET_RE.search(text):
        counts["possible_secret_assignments"] += 1


def audit_csv(path: Path, root: Path) -> dict:
    counts: Counter = Counter()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        sensitive_headers = [col for col in fields if SENSITIVE_HEADER_RE.search(col)]
        rows = 0
        for row in reader:
            rows += 1
            for value in row.values():
                if value:
                    detect(str(value), counts)
    granular = rows > 0 and any(
        name.lower() in ("ticket_id", "start_utc", "created_utc", "end_utc")
        for name in fields
    )
    return {
        "file": path.relative_to(root).as_posix(),
        "type": "csv",
        "rows_scanned": rows,
        "columns": len(fields),
        "sensitive_column_names": sensitive_headers,
        "possible_match_counts": dict(counts),
        "individual_ticket_rows_or_timestamps": granular,
        "automatic_clearance": False,  # structural scan is NOT a compliance review
    }


def audit_pbix(path: Path, root: Path) -> dict:
    counts: Counter = Counter()
    entries = []
    skipped = []
    model_entries = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            name = info.filename
            entries.append(name)
            if "datamodel" in name.lower():
                model_entries.append(name)
            if (
                info.file_size <= PBIX_READ_LIMIT
                and (name.lower().endswith(PBIX_READABLE_SUFFIXES)
                     or name.lower().split("/")[-1] in PBIX_READABLE_NAMES)
            ):
                raw = archive.read(info)
                # Scan readable strings without echoing them into reports.
                detect(raw.decode("utf-8", errors="ignore"), counts)
                detect(raw.decode("utf-16-le", errors="ignore"), counts)
            else:
                skipped.append(name)
    return {
        "file": path.relative_to(root).as_posix(),
        "type": "pbix",
        "archive_entries": len(entries),
        "embedded_model_entries": model_entries,
        "opaque_or_large_entries_not_content_inspected": skipped,
        "possible_match_counts_in_readable_metadata": dict(counts),
        "model_contents_fully_reviewed": False,
        "automatic_clearance": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--strict", action="store_true",
                        help="Fail if explicit sensitive columns or value patterns are detected.")
    parser.add_argument("--output", type=Path,
                        help="Optional local JSON summary path (no raw personal values).")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    reports = []
    for path in sorted((root / "data" / "derived").glob("*.csv")):
        reports.append(audit_csv(path, root))
    for path in sorted((root / "powerbi").glob("*.pbix")):
        try:
            reports.append(audit_pbix(path, root))
        except (zipfile.BadZipFile, OSError) as err:
            reports.append({
                "file": path.relative_to(root).as_posix(),
                "type": "pbix",
                "error": type(err).__name__,
                "automatic_clearance": False,
            })
    high_findings = [
        r["file"] for r in reports
        if r.get("sensitive_column_names")
        or any(r.get("possible_match_counts", {}).values())
        or any(r.get("possible_match_counts_in_readable_metadata", {}).values())
        or r.get("error")
    ]
    result = {
        "scope": "repository current working tree; published derived CSVs and PBIX",
        "files_scanned": len(reports),
        "high_priority_manual_review_files": high_findings,
        "reports": reports,
        "limitations": [
            "This scanner does not prove that any file is safe to publish.",
            "IDs plus precise timestamps can permit reidentification even if no explicit email/name is present.",
            "Power BI's embedded DataModel is not semantically parsed; open PBIX in Power BI Desktop to inspect source values, relationships and query/credential settings.",
            "Removing a tracked file in a commit does not remove previously published Git history.",
            "Review original dataset licensing and applicable privacy/confidentiality requirements separately.",
        ],
    }
    safe_output = json.dumps(result, indent=2, ensure_ascii=False)
    print(safe_output)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(safe_output + "\n", encoding="utf-8")
    return 2 if args.strict and high_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
