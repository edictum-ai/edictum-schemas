"""Integrity checks binding ``fixtures/manifest.json`` to the fixture tree.

Every check runs in both directions. A file present on disk but absent from the
manifest fails, and a file declared in the manifest but absent from disk fails.
That is the property that makes the manifest usable as the authoritative
"discovered" fixture set for SDK conformance coverage reporting.

These tests deliberately do NOT use ``pytest.importorskip``. A missing parser
must fail the suite, never skip it: a conformance record that quietly stops
being checked is the exact failure this manifest exists to prevent.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "fixtures"
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"


def _load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _suite_files_on_disk(directory: Path) -> list[Path]:
    return sorted(p for p in directory.glob("*.yaml") if p.is_file())


def _suite_directories_on_disk() -> list[Path]:
    return sorted(
        p for p in FIXTURES_DIR.iterdir() if p.is_dir() and _suite_files_on_disk(p)
    )


@pytest.fixture(scope="module")
def manifest() -> dict[str, Any]:
    assert MANIFEST_PATH.is_file(), (
        f"{MANIFEST_PATH} is missing. Regenerate it with: "
        "uv run --with pyyaml python scripts/generate_fixture_manifest.py"
    )
    return _load_manifest()


def test_manifest_declares_a_known_version(manifest: dict[str, Any]) -> None:
    assert manifest["version"] == 1
    assert manifest["generated_by"] == "scripts/generate_fixture_manifest.py"


def test_declared_directories_match_disk(manifest: dict[str, Any]) -> None:
    declared = set(manifest["suites"])
    on_disk = {p.name for p in _suite_directories_on_disk()}

    undeclared = on_disk - declared
    assert not undeclared, (
        f"fixture directories exist but are not declared in the manifest: "
        f"{sorted(undeclared)}. Regenerate the manifest."
    )

    missing = declared - on_disk
    assert not missing, (
        f"manifest declares fixture directories that hold no suite files: "
        f"{sorted(missing)}. Regenerate the manifest."
    )


def test_declared_files_match_disk(manifest: dict[str, Any]) -> None:
    for directory_name, suite in manifest["suites"].items():
        directory = FIXTURES_DIR / directory_name
        declared = set(suite["files"])
        on_disk = {p.name for p in _suite_files_on_disk(directory)}

        assert declared == on_disk, (
            f"{directory_name}: manifest and disk disagree. "
            f"Only on disk: {sorted(on_disk - declared)}; "
            f"only in manifest: {sorted(declared - on_disk)}. "
            "Regenerate the manifest."
        )


def test_declared_digests_match_file_bytes(manifest: dict[str, Any]) -> None:
    """An edited fixture without a regenerated manifest is a failure."""
    for directory_name, suite in manifest["suites"].items():
        for file_name, record in suite["files"].items():
            path = FIXTURES_DIR / directory_name / file_name
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            assert actual == record["sha256"], (
                f"{directory_name}/{file_name} changed since the manifest was "
                "generated. Regenerate the manifest and commit it with the "
                "fixture change."
            )


def test_declared_fixture_ids_match_parsed_ids(manifest: dict[str, Any]) -> None:
    for directory_name, suite in manifest["suites"].items():
        for file_name, record in suite["files"].items():
            path = FIXTURES_DIR / directory_name / file_name
            parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
            actual = [fixture["id"] for fixture in parsed["fixtures"]]
            assert actual == record["fixture_ids"], (
                f"{directory_name}/{file_name}: fixture IDs drifted from the "
                "manifest. Regenerate the manifest."
            )


def test_fixture_ids_are_unique_within_a_directory(manifest: dict[str, Any]) -> None:
    for directory_name, suite in manifest["suites"].items():
        seen: dict[str, str] = {}
        duplicates: list[str] = []
        for file_name, record in suite["files"].items():
            for fixture_id in record["fixture_ids"]:
                if fixture_id in seen:
                    duplicates.append(
                        f"{fixture_id} in {file_name} and {seen[fixture_id]}"
                    )
                seen[fixture_id] = file_name
        assert not duplicates, f"{directory_name}: duplicate fixture IDs: {duplicates}"


def test_fixture_ids_are_unique_across_the_corpus(manifest: dict[str, Any]) -> None:
    """IDs address fixtures in coverage reports, so they must be globally unique."""
    locations: dict[str, list[str]] = defaultdict(list)
    for directory_name, suite in manifest["suites"].items():
        for file_name, record in suite["files"].items():
            for fixture_id in record["fixture_ids"]:
                locations[fixture_id].append(f"{directory_name}/{file_name}")

    collisions = {k: v for k, v in locations.items() if len(v) > 1}
    assert not collisions, f"fixture IDs used in more than one suite: {collisions}"


def test_totals_match_the_declared_suites(manifest: dict[str, Any]) -> None:
    suites = manifest["suites"]
    expected_files = sum(len(suite["files"]) for suite in suites.values())
    expected_fixtures = sum(suite["fixture_count"] for suite in suites.values())

    assert manifest["totals"]["directories"] == len(suites)
    assert manifest["totals"]["files"] == expected_files
    assert manifest["totals"]["fixtures"] == expected_fixtures

    for directory_name, suite in suites.items():
        counted = sum(len(record["fixture_ids"]) for record in suite["files"].values())
        assert suite["fixture_count"] == counted, (
            f"{directory_name}: declared fixture_count does not match its files"
        )


def test_every_declared_directory_is_documented(manifest: dict[str, Any]) -> None:
    """A suite nobody documented is a suite nobody will run."""
    readme = (FIXTURES_DIR / "README.md").read_text(encoding="utf-8")
    undocumented = [
        name for name in manifest["suites"] if f"`{name}/`" not in readme
    ]
    assert not undocumented, (
        f"fixture directories missing from fixtures/README.md: {undocumented}"
    )
