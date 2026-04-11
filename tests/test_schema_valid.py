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
    assert "workflow-v0.18/" in readme


def test_workflow_adapter_conformance_fixtures_are_discoverable() -> None:
    adapter_dir = FIXTURES_DIR / "workflow-adapter-conformance"
    assert adapter_dir.is_dir()
    assert (adapter_dir / "README.md").is_file()
    assert any(adapter_dir.glob("*.workflow-adapter.yaml"))


def test_workflow_core_fixture_suite_shape() -> None:
    yaml = pytest.importorskip("yaml")

    suite_path = FIXTURES_DIR / "workflow" / "core.workflow.yaml"
    parsed = yaml.safe_load(suite_path.read_text(encoding="utf-8"))

    assert parsed["suite"] == "workflow-core"
    assert parsed["version"] == 1
    assert "check-gated-ship" in parsed["workflows"]

    fixtures = {fixture["id"]: fixture for fixture in parsed["fixtures"]}
    no_exit_regression = fixtures["wf-009"]

    assert [step["id"] for step in no_exit_regression["steps"]] == [
        "edit-stays-in-implement",
        "verify-advances-to-local-verify",
    ]
    assert no_exit_regression["steps"][0]["call"]["tool"] == "Edit"
    assert no_exit_regression["steps"][0]["expect"]["active_stage"] == "implement"
    assert no_exit_regression["steps"][1]["call"]["tool"] == "Bash"
    assert no_exit_regression["steps"][1]["expect"]["active_stage"] == "local-verify"
    assert no_exit_regression["steps"][1]["expect"]["evidence"]["stage_calls"] == {
        "local-verify": ["npm test"]
    }

    check_before_advance = fixtures["wf-010"]
    step = check_before_advance["steps"][0]

    assert check_before_advance["workflow"] == "check-gated-ship"
    assert step["id"] == "push-stays-blocked-in-implement"
    assert step["call"]["tool"] == "Bash"
    assert step["call"]["args"]["command"] == "git push origin feature-branch"
    assert step["execution"] == "not_run"
    assert step["expect"]["decision"] == "deny"
    assert step["expect"]["active_stage"] == "implement"
    assert step["expect"]["completed_stages"] == []
    assert step["expect"]["message_contains"] == "Push belongs in ship"


def test_workflow_adapter_conformance_fixture_suite_shape() -> None:
    yaml = pytest.importorskip("yaml")

    suite_path = (
        FIXTURES_DIR / "workflow-adapter-conformance" / "core.workflow-adapter.yaml"
    )
    parsed = yaml.safe_load(suite_path.read_text(encoding="utf-8"))

    assert parsed["suite"] == "workflow-adapter-conformance-core"
    assert parsed["version"] == 2

    fixtures = {fixture["id"]: fixture for fixture in parsed["fixtures"]}
    set_stage_regression = fixtures["wac-008"]
    step = set_stage_regression["steps"][0]

    assert step["set_stage_to"] == "local-review"
    assert "call" not in step
    assert "execution" not in step
    assert "decision" not in step["expect"]

    expected_pending = {
        "required": True,
        "stage_id": "local-review",
        "message": "Approve after reviewing the diff and pytest output",
    }
    assert step["expect"]["pending_approval"] == expected_pending

    event = step["expect"]["audit_events"][0]
    assert event["action"] == "workflow_state_updated"
    assert event["workflow"]["active_stage"] == "local-review"
    assert event["workflow"]["completed_stages"] == [
        "read-analyze",
        "implement",
        "local-verify",
    ]
    assert event["workflow"]["pending_approval"] == expected_pending


def test_workflow_coding_guard_fixtures_are_discoverable() -> None:
    coding_guard_dir = FIXTURES_DIR / "workflow-coding-guard"
    assert coding_guard_dir.is_dir()
    assert (coding_guard_dir / "README.md").is_file()
    assert any(coding_guard_dir.glob("*.workflow-coding-guard.yaml"))


def test_workflow_v0_18_fixtures_are_discoverable() -> None:
    v018_dir = FIXTURES_DIR / "workflow-v0.18"
    assert v018_dir.is_dir()
    assert (v018_dir / "README.md").is_file()
    assert any(v018_dir.glob("*.workflow-v0.18.yaml"))


def test_workflow_v0_18_wildcard_tools_suite_shape() -> None:
    yaml = pytest.importorskip("yaml")

    suite_path = FIXTURES_DIR / "workflow-v0.18" / "wildcard-tools.workflow-v0.18.yaml"
    parsed = yaml.safe_load(suite_path.read_text(encoding="utf-8"))

    assert parsed["suite"] == "workflow-v0.18-wildcard-tools"
    assert parsed["version"] == 1
    assert set(parsed["workflows"]) == {"mcp-restricted", "mixed-tools", "namespace-restricted"}

    mcp_restricted = parsed["workflows"]["mcp-restricted"]
    assert mcp_restricted["stages"][0]["tools"] == ["mcp__*"]

    mixed = parsed["workflows"]["mixed-tools"]
    assert mixed["stages"][0]["tools"] == ["Read", "mcp__*"]

    fixtures = {f["id"]: f for f in parsed["fixtures"]}
    assert set(fixtures) == {"wt-001", "wt-002", "wt-003", "wt-004"}

    # wt-001: mcp tool allowed
    wt001_step = fixtures["wt-001"]["steps"][0]
    assert wt001_step["call"]["tool"] == "mcp__github__list_prs"
    assert wt001_step["expect"]["decision"] == "allow"

    # wt-002: non-mcp tools blocked
    wt002_steps = fixtures["wt-002"]["steps"]
    assert all(s["expect"]["decision"] == "deny" for s in wt002_steps)

    # wt-004: narrower namespace blocks sibling namespace
    wt004 = fixtures["wt-004"]
    ns_workflow = parsed["workflows"]["namespace-restricted"]
    assert ns_workflow["stages"][0]["tools"] == ["mcp__ci__*"]
    allowed_step = wt004["steps"][0]
    blocked_step = wt004["steps"][1]
    assert allowed_step["expect"]["decision"] == "allow"
    assert blocked_step["expect"]["decision"] == "deny"


def test_workflow_v0_18_terminal_stage_suite_shape() -> None:
    yaml = pytest.importorskip("yaml")

    suite_path = FIXTURES_DIR / "workflow-v0.18" / "terminal-stage.workflow-v0.18.yaml"
    parsed = yaml.safe_load(suite_path.read_text(encoding="utf-8"))

    assert parsed["suite"] == "workflow-v0.18-terminal-stage"
    assert parsed["version"] == 1
    assert set(parsed["workflows"]) == {"work-then-done", "gated-terminal"}

    done_stage = parsed["workflows"]["work-then-done"]["stages"][1]
    assert done_stage["id"] == "done"
    assert done_stage["terminal"] is True
    assert "tools" not in done_stage

    gated_terminal_stage = parsed["workflows"]["gated-terminal"]["stages"][1]
    assert gated_terminal_stage["id"] == "verify-and-finish"
    assert gated_terminal_stage["terminal"] is True
    assert gated_terminal_stage["tools"] == ["Bash"]
    assert len(gated_terminal_stage["exit"]) == 1

    fixtures = {f["id"]: f for f in parsed["fixtures"]}
    assert set(fixtures) == {"ts-001", "ts-002", "ts-003", "ts-004"}

    # ts-001: all calls denied in terminal with no tools
    assert all(s["expect"]["decision"] == "deny" for s in fixtures["ts-001"]["steps"])

    # ts-002: allowed tool accepted before exit conditions are met
    ts002_step = fixtures["ts-002"]["steps"][0]
    assert ts002_step["expect"]["decision"] == "allow"
    assert ts002_step["expect"]["active_stage"] == "verify-and-finish"

    # ts-003: denied after exit conditions met
    assert all(s["expect"]["decision"] == "deny" for s in fixtures["ts-003"]["steps"])

    # ts-004: auto-advance to terminal then deny
    ts004_steps = fixtures["ts-004"]["steps"]
    assert ts004_steps[0]["expect"]["decision"] == "allow"
    assert ts004_steps[0]["expect"]["active_stage"] == "implement"
    assert ts004_steps[1]["expect"]["decision"] == "deny"
    assert ts004_steps[1]["expect"]["active_stage"] == "done"
    assert ts004_steps[1]["expect"]["completed_stages"] == ["implement"]


def test_workflow_v0_18_mcp_result_evidence_suite_shape() -> None:
    yaml = pytest.importorskip("yaml")

    suite_path = (
        FIXTURES_DIR / "workflow-v0.18" / "mcp-result-evidence.workflow-v0.18.yaml"
    )
    parsed = yaml.safe_load(suite_path.read_text(encoding="utf-8"))

    assert parsed["suite"] == "workflow-v0.18-mcp-result-evidence"
    assert parsed["version"] == 1

    check_ci = parsed["workflows"]["ci-gated-deploy"]["stages"][0]
    assert check_ci["id"] == "check-ci"
    assert check_ci["tools"] == ["mcp__ci__*"]
    assert check_ci["exit"][0]["condition"] == (
        'mcp_result_matches("mcp__ci__status", "outcome", "passing")'
    )

    fixtures = {f["id"]: f for f in parsed["fixtures"]}
    assert set(fixtures) == {"mr-001", "mr-002", "mr-003", "mr-004", "mr-005"}

    # mr-001: successful call records result
    mr001_step = fixtures["mr-001"]["steps"][0]
    assert mr001_step["mcp_result"]["outcome"] == "passing"
    assert mr001_step["execution"] == "success"
    recorded = mr001_step["expect"]["evidence"]["mcp_results"]["mcp__ci__status"]
    assert recorded[0]["outcome"] == "passing"

    # mr-002: gate passes and stage advances
    mr002_step = fixtures["mr-002"]["steps"][0]
    assert mr002_step["expect"]["decision"] == "allow"
    assert mr002_step["expect"]["active_stage"] == "deploy"

    # mr-003: gate blocks when result does not match
    mr003_step = fixtures["mr-003"]["steps"][0]
    assert mr003_step["expect"]["decision"] == "deny"
    assert "message_contains" in mr003_step["expect"]

    # mr-004: failed execution does not record result
    mr004_step = fixtures["mr-004"]["steps"][0]
    assert mr004_step["execution"] == "error"
    assert mr004_step["expect"]["evidence"]["mcp_results"] == {}

    # mr-005: no evidence → gate blocks
    mr005_step = fixtures["mr-005"]["steps"][0]
    assert mr005_step["expect"]["decision"] == "deny"
    assert fixtures["mr-005"]["initial_state"]["evidence"]["mcp_results"] == {}


def test_workflow_v0_18_extends_inheritance_suite_shape() -> None:
    yaml = pytest.importorskip("yaml")

    suite_path = (
        FIXTURES_DIR / "workflow-v0.18" / "extends-inheritance.workflow-v0.18.yaml"
    )
    parsed = yaml.safe_load(suite_path.read_text(encoding="utf-8"))

    assert parsed["suite"] == "workflow-v0.18-extends-inheritance"
    assert parsed["version"] == 1

    rulesets = parsed["rulesets"]
    assert set(rulesets) == {"base-security", "extended-security", "override-mode"}

    # parent has one rule
    assert len(rulesets["base-security"]["rules"]) == 1
    assert rulesets["base-security"]["rules"][0]["id"] == "block-push-main"

    # child extends parent and adds its own rule
    assert rulesets["extended-security"]["extends"] == "base-security"
    assert len(rulesets["extended-security"]["rules"]) == 1
    assert rulesets["extended-security"]["rules"][0]["id"] == "block-force-push"

    # override-mode extends parent but changes defaults.mode
    assert rulesets["override-mode"]["extends"] == "base-security"
    assert rulesets["override-mode"]["defaults"]["mode"] == "observe"

    fixtures = {f["id"]: f for f in parsed["fixtures"]}
    assert set(fixtures) == {"ex-001", "ex-002", "ex-003", "ex-004", "ex-005"}

    # ex-001: parent rule inherited
    assert fixtures["ex-001"]["contract"] == "extended-security"
    assert fixtures["ex-001"]["expected"]["verdict"] == "denied"
    assert "base policy" in fixtures["ex-001"]["expected"]["message_contains"]

    # ex-002: child rule enforced
    assert fixtures["ex-002"]["expected"]["verdict"] == "denied"
    assert "extended policy" in fixtures["ex-002"]["expected"]["message_contains"]

    # ex-003: unmatched call is allowed
    assert fixtures["ex-003"]["expected"]["verdict"] == "allowed"

    # ex-004: parent alone does not enforce child rule
    assert fixtures["ex-004"]["contract"] == "base-security"
    assert fixtures["ex-004"]["expected"]["verdict"] == "allowed"

    # ex-005: child overrides defaults.mode to observe → no block
    assert fixtures["ex-005"]["contract"] == "override-mode"
    assert fixtures["ex-005"]["expected"]["verdict"] == "allowed"


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
