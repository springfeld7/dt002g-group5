"""Summary-log writer utilities for verification outcomes.

This module owns summary_log persistence so verification logic can remain
focused on semantic checks (SRP).

Rows written by this module:
- Per-snippet rows: [snippet_id, status, reason]
    where status is 1 (pass) or 0 (fail).
- Aggregate row: ["TOTAL", "<ok>/<processed>", "processed=...; parse_skipped=...; success_rate=..."]
"""

import csv
import os
from typing import Any


def write_summary(
    snippet_id: str,
    verified: bool,
    errors: list[str],
    log_path: str = "summary_log.csv",
    writer: Any | None = None,
) -> None:
    """Write one per-snippet summary row.

    Args:
        snippet_id (str): Stable identifier for the processed snippet.
        verified (bool): Verification outcome for the snippet.
        errors (list[str]): Verification errors collected for the snippet.
        log_path (str): Destination CSV path when ``writer`` is not provided.
        writer (Any | None): Optional csv.writer-compatible object.
            If provided, this function writes directly to that writer and does
            not open files itself.
    """
    status = 1 if verified else 0
    reason = "" if verified else (" | ".join(errors) if errors else "Unknown Mismatch")
    row = [snippet_id, status, reason]

    if writer is not None:
        writer.writerow(row)
        return

    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    with open(log_path, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


def write_summary_totals(
    parsed_ok: int,
    parse_skipped: int,
    verified_ok: int,
    verified_fail: int,
    log_path: str = "summary_log.csv",
    writer: Any | None = None,
) -> None:
    """Write aggregate metrics as a final TOTAL row.

    Args:
        parsed_ok (int): Number of snippets parsed successfully.
        parse_skipped (int): Number of snippets skipped at parse stage.
        verified_ok (int): Number of snippets that passed verification.
        verified_fail (int): Number of snippets that failed verification.
        log_path (str): Destination CSV path when ``writer`` is not provided.
        writer (Any | None): Optional csv.writer-compatible object.
            If provided, this function writes directly to that writer and does
            not open files itself.
    """
    processed = verified_ok + verified_fail
    success_rate = (verified_ok / processed) if processed else 0.0
    row = [
        "TOTAL",
        f"{verified_ok}/{processed}",
        (
            f"processed={processed}; "
            f"parse_skipped={parse_skipped}; "
            f"success_rate={success_rate:.4f}"
        ),
    ]

    if writer is not None:
        writer.writerow(row)
        return

    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    with open(log_path, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)
