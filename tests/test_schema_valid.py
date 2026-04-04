"""Validate the edictum-v1 schema is well-formed and has expected structure."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from edictum_schemas import load_schema, schema_path


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "fixtures"


def test_schema_file_exists() -> None:
    path = schema_path()
    assert path.exists(), f"Schema file not found: {path}"
    assert path.suffix == ".json"


def test_schema_is_valid_json() -> None:
    raw = schema_path().read_text(encoding="utf-8")
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)


def test_schema_top_level_keys() -> None:
    schema = load_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "https://edictum.dev/schemas/edictum-v2-ruleset.json"
    assert schema["title"] == "Edictum Ruleset v2"
    assert schema["type"] == "object"


def test_schema_required_fields() -> None:
    schema = load_schema()
    required = schema["required"]
    assert "apiVersion" in required
    assert "kind" in required
    assert "metadata" in required
    assert "defaults" in required
    assert "rules" in required


def test_schema_defs_present() -> None:
    schema = load_schema()
    defs = schema["$defs"]
    expected_defs = [
        "Contract",
        "PreContract",
        "PostContract",
        "SessionContract",
        "SandboxContract",
        "Expression",
        "Operator",
        "Metadata",
        "Defaults",
        "Mode",
    ]
    for name in expected_defs:
        assert name in defs, f"Missing $defs/{name}"


def test_matches_operator_description() -> None:
    schema = load_schema()
    matches_desc = schema["$defs"]["Operator"]["properties"]["matches"]["description"]
    assert "10,000" in matches_desc
    assert "Python" not in matches_desc


def test_fixture_readme_lists_public_fixture_classes() -> None:
    readme = (FIXTURES_DIR / "README.md").read_text(encoding="utf-8")
    assert "behavioral/" in readme
    assert "adversarial/" in readme
    assert "rejection/" in readme
    assert "workflow/" in readme
    assert "workflow-adapter-conformance/" in readme
    assert "workflow-coding-guard/" in readme


def test_workflow_adapter_conformance_fixtures_are_discoverable() -> None:
    adapter_dir = FIXTURES_DIR / "workflow-adapter-conformance"
    assert adapter_dir.is_dir()
    assert (adapter_dir / "README.md").is_file()
    assert any(adapter_dir.glob("*.workflow-adapter.yaml"))


def test_workflow_coding_guard_fixtures_are_discoverable() -> None:
    coding_guard_dir = FIXTURES_DIR / "workflow-coding-guard"
    assert coding_guard_dir.is_dir()
    assert (coding_guard_dir / "README.md").is_file()
    assert any(coding_guard_dir.glob("*.workflow-coding-guard.yaml"))


def test_workflow_coding_guard_fixture_suite_shape() -> None:
    yaml = pytest.importorskip("yaml")

    suite_path = (
        FIXTURES_DIR / "workflow-coding-guard" / "core.workflow-coding-guard.yaml"
    )
    parsed = yaml.safe_load(suite_path.read_text(encoding="utf-8"))

    assert parsed["suite"] == "workflow-coding-guard-core"
    assert parsed["version"] == 1
    assert list(parsed["workflows"]) == ["coding-guard"]

    workflow = parsed["workflows"]["coding-guard"]
    assert workflow["kind"] == "Workflow"
    assert [stage["id"] for stage in workflow["stages"]] == [
        "read-analyze",
        "create-branch",
        "baseline-verify",
        "implement",
        "local-verify",
        "external-review",
        "docs-update",
        "push-pr",
        "ci-green",
        "done",
    ]

    fixtures = parsed["fixtures"]
    assert [fixture["id"] for fixture in fixtures] == [
        "wcg-001",
        "wcg-002",
        "wcg-003",
        "wcg-004",
        "wcg-005",
        "wcg-006",
    ]

    happy_path = fixtures[0]
    assert happy_path["steps"][-1]["expect"]["active_stage"] == "done"
    assert happy_path["steps"][6]["approval_outcomes"] == ["approved"]

    reset_targets = [
        step["reset_to"]
        for fixture in fixtures
        for step in fixture["steps"]
        if "reset_to" in step
    ]
    assert reset_targets == ["implement", "implement"]
