"""Regression tests for the unmarked-skip-as-fail guard in ``tests/conftest.py``.

A module-level ``pytest.importorskip`` is a collection skip. The runtest hook
never fires for that module, so a sibling passing test used to keep the process
exit code at 0. These tests run pytest in an isolated tree that copies the
real conftest, so reverting the collection-skip gate turns them red.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CONFTEST = Path(__file__).resolve().parent / "conftest.py"


def _run_isolated_pytest(tmp_path: Path, files: dict[str, str]) -> subprocess.CompletedProcess[str]:
    (tmp_path / "conftest.py").write_text(CONFTEST.read_text(encoding="utf-8"), encoding="utf-8")
    for name, source in files.items():
        (tmp_path / name).write_text(source, encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(tmp_path), "-q"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )


def test_module_level_importorskip_fails_the_run_when_other_tests_pass(
    tmp_path: Path,
) -> None:
    """Collection skip + a passing sibling must not stay green."""
    result = _run_isolated_pytest(
        tmp_path,
        {
            "test_missing_dep.py": (
                "import pytest\n"
                "pytest.importorskip('definitely_not_installed_xyz_12345')\n"
                "\n"
                "def test_never_runs() -> None:\n"
                "    assert True\n"
            ),
            "test_ok.py": "def test_ok() -> None:\n    assert True\n",
        },
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0, (
        "a module-level importorskip disappeared from the run while pytest "
        f"exited 0:\n{output}"
    )
    assert "skipped during collection" in output


def test_optional_skip_marker_still_allows_a_function_level_skip(tmp_path: Path) -> None:
    result = _run_isolated_pytest(
        tmp_path,
        {
            "test_optional.py": (
                "import pytest\n"
                "\n"
                "@pytest.mark.optional_skip('documented optional path')\n"
                "def test_optional() -> None:\n"
                "    pytest.skip('allowed')\n"
            ),
        },
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "skipped" in output
