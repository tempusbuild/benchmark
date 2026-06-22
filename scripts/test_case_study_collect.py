"""Unit tests for case_study_collect pure logic (no GitHub API calls)."""

import pytest

from case_study_collect import (
    WorkflowRun,
    median_seconds,
    render_comparison,
    run_wall_clock_seconds,
    successful,
    summarize,
)


def _run(started: str, ended: str, conclusion: str = "success") -> WorkflowRun:
    return {"run_started_at": started, "updated_at": ended, "conclusion": conclusion}


def test_wall_clock_from_timestamps() -> None:
    run = _run("2026-06-19T12:00:00Z", "2026-06-19T12:06:50Z")
    assert run_wall_clock_seconds(run) == 410


def test_successful_filters_out_failures() -> None:
    runs = [
        _run("2026-06-19T12:00:00Z", "2026-06-19T12:05:00Z", "success"),
        _run("2026-06-19T12:00:00Z", "2026-06-19T12:05:00Z", "failure"),
    ]
    assert len(successful(runs)) == 1


def test_summarize_takes_median_and_latest_date() -> None:
    runs = [
        _run("2026-06-17T10:00:00Z", "2026-06-17T10:04:00Z"),  # 240s
        _run("2026-06-19T10:00:00Z", "2026-06-19T10:03:00Z"),  # 180s (latest date)
        _run("2026-06-18T10:00:00Z", "2026-06-18T10:10:00Z"),  # 600s (outlier)
    ]
    result = summarize("ubuntu-latest", runs)
    assert result.runs == 3
    assert result.median_seconds == 240
    assert result.date == "2026-06-19"


def test_median_rejects_empty() -> None:
    with pytest.raises(ValueError, match="no successful runs"):
        median_seconds([])


def test_render_comparison_has_both_rows_and_speedup() -> None:
    github = summarize(
        "ubuntu-latest", [_run("2026-06-19T00:00:00Z", "2026-06-19T00:08:00Z")]
    )
    tempus = summarize(
        "tempus-ubuntu-24.04-4core",
        [_run("2026-06-19T00:00:00Z", "2026-06-19T00:04:00Z")],
    )
    out = render_comparison(
        "pallets/flask", "22d924701a6ae2e4cd01e9a15bbaf3946094af65", github, tempus
    )
    assert "`pallets/flask`" in out
    assert "`22d9247`" in out  # ref shortened
    assert "480s" in out and "240s" in out
    assert "2.00x" in out
