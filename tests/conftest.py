"""Make an unexpectedly skipped test a failure.

Before 2026-08-15 this suite ran in CI without PyYAML installed. Every test that
read fixture content called ``pytest.importorskip("yaml")``, so 7 of 17 tests
skipped and the suite reported green — no fixture content was verified at all
for months.

A skip that nobody notices is a check that stopped running. Tests that must be
allowed to skip declare it explicitly::

    @pytest.mark.optional_skip("darwin-only path semantics")
    def test_something() -> None:
        ...
"""

from __future__ import annotations

from typing import Any

import pytest

_OPTIONAL_SKIP = "optional_skip"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        f"{_OPTIONAL_SKIP}(reason): this test is allowed to skip; everything else "
        "that skips fails the run",
    )


# wrapper=True (the current-style hook wrapper) instead of the deprecated
# hookwrapper=True: CI installs an unpinned pytest, and the old protocol is
# removed in pytest 9 — the guard must survive that upgrade.
@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: Any):
    report = yield
    if report.skipped and item.get_closest_marker(_OPTIONAL_SKIP) is None:
        report.outcome = "failed"
        reason = report.longrepr[2] if isinstance(report.longrepr, tuple) else report.longrepr
        report.longrepr = (
            f"{item.nodeid} skipped without an @pytest.mark.{_OPTIONAL_SKIP} marker: "
            f"{reason}\n"
            "An unmarked skip means a check silently stopped running. Install the "
            "missing dependency, or mark the test as legitimately optional."
        )
    return report
