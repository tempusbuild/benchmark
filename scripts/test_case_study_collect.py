"""Unit tests for case_study_collect pure logic (no GitHub API calls)."""

import pytest

from case_study_collect import (
    JobTiming,
    median_seconds,
    render_comparison,
    successful,
    summarize,
    wall_clock_seconds,
)


def _job(started: str, ended: str, conclusion: str = "success") -> JobTiming:
    return {"started_at": started, "completed_at": ended, "conclusion": conclusion}


def test_wall_clock_from_timestamps() -> None:
    job = _job("2026-06-19T12:00:00Z", "2026-06-19T12:06:50Z")
    assert wall_clock_seconds(job) == 410


def test_successful_filters_out_failures() -> None:
    jobs = [
        _job("2026-06-19T12:00:00Z", "2026-06-19T12:05:00Z", "success"),
        _job("2026-06-19T12:00:00Z", "2026-06-19T12:05:00Z", "failure"),
    ]
    assert len(successful(jobs)) == 1


def test_summarize_takes_median_and_latest_date() -> None:
    jobs = [
        _job("2026-06-17T10:00:00Z", "2026-06-17T10:04:00Z"),  # 240s
        _job("2026-06-19T10:00:00Z", "2026-06-19T10:03:00Z"),  # 180s (latest date)
        _job("2026-06-18T10:00:00Z", "2026-06-18T10:10:00Z"),  # 600s (outlier)
    ]
    result = summarize("ubuntu-latest", jobs)
    assert result.runs == 3
    assert result.median_seconds == 240
    assert result.date == "2026-06-19"


def test_median_rejects_empty() -> None:
    with pytest.raises(ValueError, match="no successful runs"):
        median_seconds([])


def test_render_comparison_has_both_rows_and_speedup() -> None:
    github = summarize(
        "ubuntu-latest", [_job("2026-06-19T00:00:00Z", "2026-06-19T00:08:00Z")]
    )
    tempus = summarize(
        "tempus-ubuntu-24.04-4core",
        [_job("2026-06-19T00:00:00Z", "2026-06-19T00:04:00Z")],
    )
    out = render_comparison(
        "django/django", "ee93f65169c280c9ab3d2ce103dd478c96d05065", github, tempus
    )
    assert "`django/django`" in out
    assert "`ee93f65`" in out  # ref shortened
    assert "480s" in out and "240s" in out
    assert "2.00x" in out
