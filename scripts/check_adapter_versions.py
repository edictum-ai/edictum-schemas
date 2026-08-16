#!/usr/bin/env python3
"""Fail if the adapter version record is malformed, stale, or out of sync.

``invariants/adapter-versions.json`` and the Markdown table in
``invariants/ADAPTER_VERSION_POLICY.md`` are the two copies of the L1.0
version record. CI and pre-commit run this check so a weekly update cannot
leave malformed JSON, a stale ``measured_at``, or disagreement between the
copies while the suite stays green.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "invariants" / "ADAPTER_VERSION_POLICY.md"
RECORD_PATH = REPO_ROOT / "invariants" / "adapter-versions.json"

REQUIRED_TOP_LEVEL = (
    "measured_at",
    "cadence",
    "adapters",
    "owners",
    "when_latest_breaks",
)
REQUIRED_ADAPTER = (
    "id",
    "language",
    "package",
    "seam",
    "first_seam_version",
    "first_seam_evidence",
    "floor",
    "latest_inspected",
    "unsupported_below",
    "notes",
)
# Universally required values. first_seam_version and floor may be null
# together only for an explicit no-seam adapter (LangChainGo).
REQUIRED_ADAPTER_NONEMPTY = (
    "package",
    "seam",
    "latest_inspected",
    "unsupported_below",
    "notes",
)
NULLABLE_ADAPTER = (
    "first_seam_version",
    "floor",
)
# Adapters with a native seam must keep both version fields as non-empty
# strings and unsupported_below equal to floor. Nulls are allowed only on
# this explicit no-seam set, and only when first_seam_version and floor
# are null together; those records must use the canonical
# unsupported_below token (NO_NATIVE_SEAM_UNSUPPORTED_BELOW).
NO_NATIVE_SEAM_ADAPTERS = frozenset({"langchaingo"})
NO_NATIVE_SEAM_UNSUPPORTED_BELOW = "all (no native block seam)"
TABLE_FIELDS = ("id", "owner", "package", "seam", "first", "floor", "latest", "evidence")
WEEKLY_MAX_AGE_DAYS = 7


class RecordError(ValueError):
    """Adapter version record is not fit to ship."""


def _cell(value: Any) -> str:
    if value is None:
        return "None"
    return str(value)


def _normalize_evidence(value: str) -> str:
    """Markdown tables cannot contain raw pipes, so JSON uses ``|`` and the table uses ``/``."""
    return value.replace("|", "/")


def parse_markdown_table(markdown: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            # Skip blank lines so a mid-table empty line does not silently
            # drop the remaining rows and surface as an id-order mismatch.
            if header is not None and stripped:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if header is None:
            if cells[:1] != ["id"]:
                continue
            if tuple(cells) != TABLE_FIELDS:
                raise RecordError(
                    f"policy table header {cells} does not match {list(TABLE_FIELDS)}"
                )
            header = cells
            continue
        if all(set(c) <= {"-", ":"} and c for c in cells):
            continue
        if len(cells) != len(header):
            raise RecordError(
                f"policy table row has {len(cells)} cells, expected {len(header)}: {cells[0]!r}"
            )
        rows.append(dict(zip(header, cells)))
    if not rows:
        raise RecordError("policy markdown has no adapter version table rows")
    return rows


def load_record(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RecordError(f"cannot read {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RecordError(f"{path} is malformed JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RecordError(f"{path} must be a JSON object")
    return data


def check_record_shape(record: dict[str, Any]) -> None:
    missing = [k for k in REQUIRED_TOP_LEVEL if k not in record]
    if missing:
        raise RecordError(f"record missing top-level keys: {missing}")
    when_latest_breaks = record["when_latest_breaks"]
    if not isinstance(when_latest_breaks, str) or not when_latest_breaks.strip():
        raise RecordError("when_latest_breaks must be a non-empty string")
    if record["cadence"] != "weekly":
        raise RecordError(f"cadence must be 'weekly', got {record['cadence']!r}")
    adapters = record["adapters"]
    if not isinstance(adapters, list) or not adapters:
        raise RecordError("adapters must be a non-empty list")
    owners = record["owners"]
    if not isinstance(owners, dict):
        raise RecordError("owners must be an object")
    for language, owner in owners.items():
        if not isinstance(owner, str) or not owner.strip():
            raise RecordError(f"owners[{language!r}] must be a non-empty string")
    seen: set[str] = set()
    for adapter in adapters:
        if not isinstance(adapter, dict):
            raise RecordError("each adapter must be an object")
        missing_a = [k for k in REQUIRED_ADAPTER if k not in adapter]
        if missing_a:
            raise RecordError(f"adapter {adapter.get('id')!r} missing keys: {missing_a}")
        adapter_id = adapter["id"]
        if not isinstance(adapter_id, str) or not adapter_id:
            raise RecordError("adapter id must be a non-empty string")
        if adapter_id in seen:
            raise RecordError(f"duplicate adapter id: {adapter_id}")
        seen.add(adapter_id)
        language = adapter["language"]
        if language not in owners:
            raise RecordError(f"{adapter_id}: language {language!r} has no owner")
        evidence = adapter["first_seam_evidence"]
        if not isinstance(evidence, str) or not evidence.strip():
            raise RecordError(f"{adapter_id}: first_seam_evidence must be a non-empty string")
        for key in REQUIRED_ADAPTER_NONEMPTY:
            value = adapter[key]
            if not isinstance(value, str) or not value.strip():
                raise RecordError(f"{adapter_id}: {key} must be a non-empty string")
        first = adapter["first_seam_version"]
        floor = adapter["floor"]
        first_null = first is None
        floor_null = floor is None
        if first_null != floor_null:
            raise RecordError(
                f"{adapter_id}: first_seam_version and floor must both be null "
                "or both be non-empty strings"
            )
        if first_null:
            if adapter_id not in NO_NATIVE_SEAM_ADAPTERS:
                raise RecordError(
                    f"{adapter_id}: first_seam_version and floor may be null "
                    "only for adapters without a native seam"
                )
            unsupported_below = adapter["unsupported_below"]
            if unsupported_below != NO_NATIVE_SEAM_UNSUPPORTED_BELOW:
                raise RecordError(
                    f"{adapter_id}: unsupported_below must be "
                    f"{NO_NATIVE_SEAM_UNSUPPORTED_BELOW!r} for adapters "
                    f"without a native seam, got {unsupported_below!r}"
                )
        else:
            for key in NULLABLE_ADAPTER:
                value = adapter[key]
                if not isinstance(value, str) or not value.strip():
                    raise RecordError(
                        f"{adapter_id}: {key} must be a non-empty string"
                    )
            unsupported_below = adapter["unsupported_below"]
            if unsupported_below != floor:
                raise RecordError(
                    f"{adapter_id}: unsupported_below must equal floor "
                    f"for native-seam adapters, got {unsupported_below!r} != {floor!r}"
                )


def check_measured_at(record: dict[str, Any], *, today: date | None = None) -> None:
    raw = record["measured_at"]
    if not isinstance(raw, str):
        raise RecordError("measured_at must be an ISO date string")
    try:
        measured = date.fromisoformat(raw)
    except ValueError as exc:
        raise RecordError(f"measured_at {raw!r} is not an ISO date") from exc
    if today is None:
        today = datetime.now(timezone.utc).date()
    if measured > today:
        raise RecordError(f"measured_at {measured.isoformat()} is in the future")
    age = (today - measured).days
    if age >= WEEKLY_MAX_AGE_DAYS:
        raise RecordError(
            f"measured_at {measured.isoformat()} is {age} days old; "
            f"weekly cadence is stale at {WEEKLY_MAX_AGE_DAYS} days"
        )


def parse_markdown_metadata(markdown: str) -> dict[str, str]:
    """Read cadence, owner summary, and break-response from the policy prose."""
    cadence = ""
    owner_summary = ""
    when_latest_breaks = ""
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("Cadence:"):
            rest = stripped[len("Cadence:") :].strip()
            cadence_part, sep, owner_part = rest.partition("Owner:")
            cadence = cadence_part.strip().rstrip(".")
            if sep:
                owner_raw = owner_part.strip()
                if "(" in owner_raw:
                    owner_raw = owner_raw.split("(", 1)[0]
                owner_summary = owner_raw.strip().rstrip(".")
        elif stripped.startswith("When latest breaks:"):
            when_latest_breaks = stripped.split(":", 1)[1].strip()
    missing = [
        name
        for name, value in (
            ("cadence", cadence),
            ("owner summary", owner_summary),
            ("when latest breaks", when_latest_breaks),
        )
        if not value
    ]
    if missing:
        raise RecordError(f"policy markdown missing metadata: {missing}")
    return {
        "cadence": cadence,
        "owner_summary": owner_summary,
        "when_latest_breaks": when_latest_breaks,
    }


def check_copies_agree(
    record: dict[str, Any],
    table_rows: list[dict[str, str]],
    markdown: str,
) -> None:
    meta = parse_markdown_metadata(markdown)
    expected_meta = {
        "cadence": record["cadence"],
        "owner_summary": " / ".join(record["owners"].values()),
        "when_latest_breaks": record["when_latest_breaks"],
    }
    if meta != expected_meta:
        diffs = [k for k in expected_meta if meta[k] != expected_meta[k]]
        md_bits = {k: meta[k] for k in diffs}
        js_bits = {k: expected_meta[k] for k in diffs}
        raise RecordError(
            f"policy metadata disagrees on {diffs}. "
            f"markdown={md_bits} json={js_bits}"
        )
    adapters = record["adapters"]
    owners: dict[str, str] = record["owners"]
    json_ids = [a["id"] for a in adapters]
    md_ids = [r["id"] for r in table_rows]
    if json_ids != md_ids:
        raise RecordError(
            f"adapter id order/set disagrees: json={json_ids} markdown={md_ids}"
        )
    by_id = {a["id"]: a for a in adapters}
    for row in table_rows:
        adapter = by_id[row["id"]]
        expected = {
            "id": adapter["id"],
            "owner": owners[adapter["language"]],
            "package": _cell(adapter["package"]),
            "seam": _cell(adapter["seam"]),
            "first": _cell(adapter["first_seam_version"]),
            "floor": _cell(adapter["floor"]),
            "latest": _cell(adapter["latest_inspected"]),
            "evidence": _normalize_evidence(_cell(adapter["first_seam_evidence"])),
        }
        actual = {k: row[k] for k in TABLE_FIELDS}
        actual["evidence"] = _normalize_evidence(actual["evidence"])
        if actual != expected:
            diffs = [k for k in TABLE_FIELDS if actual[k] != expected[k]]
            md_bits = {k: actual[k] for k in diffs}
            js_bits = {k: expected[k] for k in diffs}
            raise RecordError(
                f"{row['id']}: markdown/JSON disagree on {diffs}. "
                f"markdown={md_bits} json={js_bits}"
            )


def check_paths(
    record_path: Path,
    policy_path: Path,
    *,
    today: date | None = None,
) -> dict[str, Any]:
    record = load_record(record_path)
    check_record_shape(record)
    check_measured_at(record, today=today)
    markdown = policy_path.read_text(encoding="utf-8")
    table_rows = parse_markdown_table(markdown)
    check_copies_agree(record, table_rows, markdown)
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, default=RECORD_PATH)
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    args = parser.parse_args(argv)
    try:
        record = check_paths(args.record, args.policy)
    except RecordError as exc:
        print(f"adapter version record: {exc}", file=sys.stderr)
        return 1
    n = len(record["adapters"])
    print(
        f"adapter version record ok: {n} adapters, "
        f"measured_at={record['measured_at']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
