#!/usr/bin/env python3
"""Reduce a case study's workflow runs into a comparison row.

A case study runs a real upstream project's own CI on two runners (tempus vs github) via two
workflows that differ only in `runs-on:`. This reads each workflow's recent runs from the GitHub
API (via `gh`), takes the median job wall-clock, and renders a Markdown comparison.

Timing is the JOB's own `started_at` .. `completed_at` (the Actions jobs API) — the wall-clock of
the job on the runner. Run-level `run_started_at` .. `updated_at` is deliberately NOT used: it also
counts run orchestration (run record -> job assignment) and finalization, which is GitHub
infrastructure overhead, differs between hosted and self-hosted runners, and would bias the
comparison. Queue time is excluded either way (`started_at` is post-assignment).

Usage:
    case_study_collect.py --repo OWNER/REPO --upstream UPSTREAM/REPO --ref UPSTREAM_SHA \
        --tempus-workflow casestudy-django-tempus.yml \
        --github-workflow casestudy-django-github.yml [--limit 3]

--repo hosts the Actions runs (this benchmark repo); --upstream is the real project the case
study exercises (shown in the table); --ref is the pinned upstream commit those runs measured.
"""

import argparse
import json
import statistics
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict


class JobTiming(TypedDict):
    """One workflow run reduced to its single job's timing (GitHub Actions jobs API)."""

    started_at: str  # when the runner began the job (post-queue/assignment)
    completed_at: str
    conclusion: str | None  # null while the run is still in progress


def wall_clock_seconds(job: JobTiming) -> float:
    """Wall-clock of the job on the runner: completed_at - started_at, in seconds."""
    started = datetime.fromisoformat(job["started_at"])
    ended = datetime.fromisoformat(job["completed_at"])
    return (ended - started).total_seconds()


def successful(jobs: list[JobTiming]) -> list[JobTiming]:
    return [j for j in jobs if j["conclusion"] == "success"]


def median_seconds(values: list[float]) -> float:
    if not values:
        raise ValueError("no successful runs to take a median of")
    return statistics.median(values)


@dataclass(frozen=True)
class VariantResult:
    label: str  # the runs-on label this variant targeted
    runs: int
    median_seconds: float
    date: str  # ISO date of the most recent run


def summarize(runner_label: str, jobs: list[JobTiming]) -> VariantResult:
    ok = successful(jobs)
    median = median_seconds([wall_clock_seconds(j) for j in ok])  # raises if empty
    latest_date = max(j["started_at"] for j in ok)[:10]  # ok is non-empty here
    return VariantResult(runner_label, len(ok), median, latest_date)


def _fmt(seconds: float) -> str:
    return f"{round(seconds)}s"


def render_comparison(
    upstream: str, ref: str, github: VariantResult, tempus: VariantResult
) -> str:
    short_ref = ref[:7]
    header = (
        "| Upstream | Ref | Runner | Runs | Median wall-clock | Date |\n"
        "| -------- | --- | ------ | ---- | ----------------- | ---- |"
    )
    rows = [
        f"| `{upstream}` | `{short_ref}` | `{github.label}` | {github.runs} | "
        f"{_fmt(github.median_seconds)} | {github.date} |",
        f"| `{upstream}` | `{short_ref}` | `{tempus.label}` | {tempus.runs} | "
        f"{_fmt(tempus.median_seconds)} | {tempus.date} |",
    ]
    speedup = (
        github.median_seconds / tempus.median_seconds if tempus.median_seconds else 0
    )
    note = (
        f"\n\nspeedup factor {speedup:.2f}x (github-hosted median / tempus median; "
        ">1 means tempus is faster) for this case study."
    )
    return "\n".join([header, *rows]) + note


def _gh_json(*api_args: str) -> object:
    """Run `gh api ARGS` and parse JSON stdout; exit cleanly (not a traceback) on failure."""
    try:
        proc = subprocess.run(
            ["gh", "api", *api_args],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(f"gh api {' '.join(api_args)} failed: {exc.stderr.strip()}")
    return json.loads(proc.stdout)


def fetch_job_timings(repo: str, workflow_file: str, limit: int) -> list[JobTiming]:
    """The `limit` most recent runs of a workflow, each reduced to its single job's timing.

    Two API hops: the runs list gives run ids + conclusion; per run the jobs API gives the job's
    started_at/completed_at (the runs list carries no job timing).
    """
    runs = _gh_json(
        f"repos/{repo}/actions/workflows/{workflow_file}/runs",
        "--jq",
        f".workflow_runs[:{limit}] | map({{id, conclusion}})",
    )
    timings: list[JobTiming] = []
    for run in runs:
        job = _gh_json(
            f"repos/{repo}/actions/runs/{run['id']}/jobs",
            "--jq",
            ".jobs[0] | {started_at, completed_at}",
        )
        timings.append(
            {
                "started_at": job["started_at"],
                "completed_at": job["completed_at"],
                "conclusion": run["conclusion"],
            }
        )
    return timings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        required=True,
        help="OWNER/REPO hosting the workflow runs (this benchmark repo)",
    )
    parser.add_argument(
        "--upstream",
        required=True,
        help="OWNER/REPO of the real project the case study runs (shown in the table)",
    )
    parser.add_argument(
        "--ref",
        required=True,
        help="pinned UPSTREAM commit the runs measured (e.g. the django sha)",
    )
    parser.add_argument("--tempus-workflow", required=True)
    parser.add_argument("--github-workflow", required=True)
    parser.add_argument(
        "--limit", type=int, default=3, help="most recent runs per workflow"
    )
    args = parser.parse_args()

    tempus = summarize(
        "tempus-ubuntu-24.04-4core",
        fetch_job_timings(args.repo, args.tempus_workflow, args.limit),
    )
    github = summarize(
        "ubuntu-latest",
        fetch_job_timings(args.repo, args.github_workflow, args.limit),
    )
    print(render_comparison(args.upstream, args.ref, github, tempus))


if __name__ == "__main__":
    main()
