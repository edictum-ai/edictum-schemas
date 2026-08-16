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

``pytest_runtest_makereport`` only sees skips that happen after a test is
scheduled. A module-level ``pytest.importorskip(...)`` is a collection skip:
the module disappears from the run and this hook never fires. Collection
reports and the session skip summary are checked so that case cannot stay green.
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


def _skip_reason(report: Any) -> object:
    if isinstance(report.longrepr, tuple) and len(report.longrepr) >= 3:
        return report.longrepr[2]
    return report.longrepr


def _fail_unmarked_skip(report: Any, *, during: str) -> None:
    report.outcome = "failed"
    report.longrepr = (
        f"{report.nodeid} skipped {during} without an @pytest.mark.{_OPTIONAL_SKIP} "
        f"marker: {_skip_reason(report)}\n"
        "An unmarked skip means a check silently stopped running. Install the "
        "missing dependency, or mark the test as legitimately optional."
    )


# wrapper=True (the current-style hook wrapper) instead of the deprecated
# hookwrapper=True: CI installs an unpinned pytest, and the old protocol is
# removed in pytest 9 — the guard must survive that upgrade.
@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: Any):
    report = yield
    if report.skipped and item.get_closest_marker(_OPTIONAL_SKIP) is None:
        _fail_unmarked_skip(report, during="during the test")
    return report


# Do not touch collector.obj here: a collection skip means import was aborted,
# and reading .obj re-imports the module and raises Skipped as INTERNALERROR.
@pytest.hookimpl(wrapper=True)
def pytest_make_collect_report(collector: pytest.Collector):
    report = yield
    if report.skipped:
        _fail_unmarked_skip(report, during="during collection")
    return report


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Fail the run if any unmarked skip is still in the terminal skip summary.

    Converting the collection-report outcome to failed (above) is the primary
    gate. This is the backstop: a skip that never produced a runtest report
    can still sit in ``reporter.stats['skipped']`` while pytest exits 0.
    """
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:
        return

    items_by_id = {item.nodeid: item for item in getattr(session, "items", [])}
    unexpected = []
    for report in reporter.stats.get("skipped", []):
        item = items_by_id.get(getattr(report, "nodeid", ""))
        if item is not None and item.get_closest_marker(_OPTIONAL_SKIP) is not None:
            continue
        unexpected.append(getattr(report, "nodeid", "<unknown>"))

    if not unexpected:
        return
    if session.exitstatus not in (
        0,
        pytest.ExitCode.OK,
        pytest.ExitCode.NO_TESTS_COLLECTED,
    ):
        return
    session.exitstatus = pytest.ExitCode.TESTS_FAILED
