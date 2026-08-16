"""The adapter version record must parse, stay fresh, and match its Markdown copy."""

from __future__ import annotations

import importlib.util
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_checker() -> Any:
    path = REPO_ROOT / "scripts" / "check_adapter_versions.py"
    spec = importlib.util.spec_from_file_location("check_adapter_versions", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


chk = _load_checker()


def _copy_record(tmp_path: Path) -> tuple[Path, Path]:
    record_path = tmp_path / "adapter-versions.json"
    policy_path = tmp_path / "ADAPTER_VERSION_POLICY.md"
    record_path.write_text(chk.RECORD_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    policy_path.write_text(chk.POLICY_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    return record_path, policy_path


def _record_today(record_path: Path) -> date:
    data = json.loads(record_path.read_text(encoding="utf-8"))
    return date.fromisoformat(data["measured_at"])


def test_committed_record_is_valid() -> None:
    chk.check_paths(chk.RECORD_PATH, chk.POLICY_PATH)


def test_malformed_json_fails(tmp_path: Path) -> None:
    record_path = tmp_path / "adapter-versions.json"
    policy_path = tmp_path / "ADAPTER_VERSION_POLICY.md"
    record_path.write_text("{not json", encoding="utf-8")
    policy_path.write_text("| id |\n", encoding="utf-8")
    with pytest.raises(chk.RecordError, match="malformed JSON"):
        chk.check_paths(record_path, policy_path)


def test_stale_measured_at_fails(tmp_path: Path) -> None:
    record_path, policy_path = _copy_record(tmp_path)
    data = json.loads(record_path.read_text(encoding="utf-8"))
    today = date(2026, 8, 16)
    data["measured_at"] = (today - timedelta(days=8)).isoformat()
    record_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(chk.RecordError, match="days old"):
        chk.check_paths(record_path, policy_path, today=today)


def test_fresh_measured_at_passes(tmp_path: Path) -> None:
    record_path, policy_path = _copy_record(tmp_path)
    data = json.loads(record_path.read_text(encoding="utf-8"))
    today = date(2026, 8, 16)
    data["measured_at"] = (today - timedelta(days=7)).isoformat()
    record_path.write_text(json.dumps(data), encoding="utf-8")
    chk.check_paths(record_path, policy_path, today=today)


def test_disagreement_fails(tmp_path: Path) -> None:
    record_path, policy_path = _copy_record(tmp_path)
    today = _record_today(record_path)
    policy = policy_path.read_text(encoding="utf-8")
    policy_path.write_text(policy.replace("| 1.3.15 |", "| 9.9.9 |", 1), encoding="utf-8")
    with pytest.raises(chk.RecordError, match="disagree"):
        chk.check_paths(record_path, policy_path, today=today)


def test_null_required_adapter_field_fails(tmp_path: Path) -> None:
    record_path, policy_path = _copy_record(tmp_path)
    today = _record_today(record_path)
    data = json.loads(record_path.read_text(encoding="utf-8"))
    data["adapters"][0]["latest_inspected"] = None
    record_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(chk.RecordError, match="latest_inspected must be a non-empty string"):
        chk.check_paths(record_path, policy_path, today=today)


def test_empty_required_adapter_field_fails(tmp_path: Path) -> None:
    record_path, policy_path = _copy_record(tmp_path)
    today = _record_today(record_path)
    data = json.loads(record_path.read_text(encoding="utf-8"))
    data["adapters"][0]["package"] = "   "
    record_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(chk.RecordError, match="package must be a non-empty string"):
        chk.check_paths(record_path, policy_path, today=today)


def test_seamed_adapter_null_floor_fails(tmp_path: Path) -> None:
    record_path, policy_path = _copy_record(tmp_path)
    today = _record_today(record_path)
    data = json.loads(record_path.read_text(encoding="utf-8"))
    seamed = next(a for a in data["adapters"] if a["id"] != "langchaingo")
    seamed["floor"] = None
    record_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(chk.RecordError, match="first_seam_version and floor"):
        chk.check_paths(record_path, policy_path, today=today)


def test_seamed_adapter_both_null_versions_fail(tmp_path: Path) -> None:
    record_path, policy_path = _copy_record(tmp_path)
    today = _record_today(record_path)
    data = json.loads(record_path.read_text(encoding="utf-8"))
    seamed = next(a for a in data["adapters"] if a["id"] != "langchaingo")
    seamed["first_seam_version"] = None
    seamed["floor"] = None
    record_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(chk.RecordError, match="without a native seam"):
        chk.check_paths(record_path, policy_path, today=today)


def test_langchaingo_null_versions_pass() -> None:
    record = json.loads(chk.RECORD_PATH.read_text(encoding="utf-8"))
    go = next(a for a in record["adapters"] if a["id"] == "langchaingo")
    assert go["first_seam_version"] is None
    assert go["floor"] is None
    chk.check_paths(chk.RECORD_PATH, chk.POLICY_PATH)


def test_blank_line_mid_table_keeps_later_rows(tmp_path: Path) -> None:
    record_path, policy_path = _copy_record(tmp_path)
    today = _record_today(record_path)
    policy = policy_path.read_text(encoding="utf-8")
    needle = "| crewai |"
    policy_path.write_text(policy.replace(needle, "\n" + needle, 1), encoding="utf-8")
    chk.check_paths(record_path, policy_path, today=today)
