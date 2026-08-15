#!/usr/bin/env python3
"""Regenerate ``fixtures/manifest.json``, the shared-fixture inventory.

The manifest is the single declared record of what the shared corpus contains:
every suite directory, every fixture file, every fixture ID, and a digest of
each file's bytes. ``tests/test_fixture_manifest.py`` compares it against the
tree in both directions, so an undeclared file, a deleted file, an edited file,
or a renamed fixture ID is a red test rather than a silent divergence.

Fixture IDs are recorded per file because SDK conformance runners report
coverage by ID: the manifest is the authoritative "discovered" set that a
runner's "executed" set is compared against.

Usage::

    uv run --with pyyaml python scripts/generate_fixture_manifest.py

Run it after adding, removing, renaming, or editing any fixture file, and
commit the regenerated manifest alongside the change.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "fixtures"
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"
MANIFEST_VERSION = 1


def fixture_files(directory: Path) -> list[Path]:
    """Return the suite files in one fixture directory, sorted by name."""
    return sorted(p for p in directory.glob("*.yaml") if p.is_file())


def suite_directories(fixtures_dir: Path) -> list[Path]:
    """Return every fixture directory holding at least one suite file."""
    return sorted(p for p in fixtures_dir.iterdir() if p.is_dir() and fixture_files(p))


def describe_file(path: Path) -> dict[str, Any]:
    """Extract the declared record for a single fixture suite file."""
    raw = path.read_bytes()
    parsed = yaml.safe_load(raw.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError(f"{path}: suite file must parse to a mapping")

    fixtures = parsed.get("fixtures")
    if not isinstance(fixtures, list):
        raise ValueError(f"{path}: suite file must declare a 'fixtures' list")

    ids: list[str] = []
    for index, fixture in enumerate(fixtures):
        if not isinstance(fixture, dict):
            raise ValueError(f"{path}: fixtures[{index}] must be a mapping")
        fixture_id = fixture.get("id")
        if not isinstance(fixture_id, str) or not fixture_id:
            raise ValueError(f"{path}: fixtures[{index}] must declare a non-empty string id")
        ids.append(fixture_id)

    return {
        "suite": parsed.get("suite"),
        "format_version": parsed.get("version"),
        "fixture_ids": ids,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def build_manifest(fixtures_dir: Path = FIXTURES_DIR) -> dict[str, Any]:
    """Build the full manifest for the fixture tree."""
    suites: dict[str, Any] = {}
    total_files = 0
    total_fixtures = 0

    for directory in suite_directories(fixtures_dir):
        files: dict[str, Any] = {}
        directory_fixtures = 0
        for path in fixture_files(directory):
            record = describe_file(path)
            files[path.name] = record
            directory_fixtures += len(record["fixture_ids"])
        suites[directory.name] = {"files": files, "fixture_count": directory_fixtures}
        total_files += len(files)
        total_fixtures += directory_fixtures

    return {
        "version": MANIFEST_VERSION,
        "generated_by": "scripts/generate_fixture_manifest.py",
        "note": (
            "Generated file — do not edit by hand. Regenerate after any fixture "
            "change and commit the result; tests/test_fixture_manifest.py fails "
            "when this manifest and the fixture tree disagree."
        ),
        "suites": suites,
        "totals": {
            "directories": len(suites),
            "files": total_files,
            "fixtures": total_fixtures,
        },
    }


def render(manifest: dict[str, Any]) -> str:
    """Render the manifest deterministically."""
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def main() -> int:
    manifest = build_manifest()
    MANIFEST_PATH.write_text(render(manifest), encoding="utf-8")
    totals = manifest["totals"]
    print(
        f"wrote {MANIFEST_PATH.relative_to(REPO_ROOT)}: "
        f"{totals['directories']} directories, "
        f"{totals['files']} files, "
        f"{totals['fixtures']} fixtures"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
