#!/usr/bin/env python3
"""Reduce a case study's workflow runs into a comparison row.

A case study runs a real upstream project's own CI on two runners (tempus vs github) via two
workflows that differ only in `runs-on:`. This reads the recent runs of each workflow from the
GitHub API (via `gh`), takes the median wall-clock, and renders a Markdown comparison.

Timing comes from the run's own start/end (`run_started_at` .. `updated_at`) because the steps
are upstream's — there is no in-workflow timer under our control.

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


class WorkflowRun(TypedDict):
    """The subset of a GitHub Actions run record this tool reads."""

    run_started_at: str
    updated_at: str
    conclusion: str | None  # null while a run is still in progress


def run_wall_clock_seconds(run: WorkflowRun) -> float:
    """Wall-clock of one workflow run: updated_at - run_started_at, in seconds."""
    started = datetime.fromisoformat(run["run_started_at"])
    ended = datetime.fromisoformat(run["updated_at"])
    return (ended - started).total_seconds()


def successful(runs: list[WorkflowRun]) -> list[WorkflowRun]:
    return [r for r in runs if r["conclusion"] == "success"]


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


def summarize(runner_label: str, runs: list[WorkflowRun]) -> VariantResult:
    ok = successful(runs)
    median = median_seconds([run_wall_clock_seconds(r) for r in ok])  # raises if empty
    latest_date = max(r["run_started_at"] for r in ok)[:10]  # ok is non-empty here
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


def fetch_runs(repo: str, workflow_file: str, limit: int) -> list[WorkflowRun]:
    try:
        proc = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{repo}/actions/workflows/{workflow_file}/runs",
                "--jq",
                f".workflow_runs[:{limit}]",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(f"gh api failed for {repo} / {workflow_file}: {exc.stderr.strip()}")
    return json.loads(proc.stdout)


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
        fetch_runs(args.repo, args.tempus_workflow, args.limit),
    )
    github = summarize(
        "ubuntu-latest",
        fetch_runs(args.repo, args.github_workflow, args.limit),
    )
    print(render_comparison(args.upstream, args.ref, github, tempus))


if __name__ == "__main__":
    main()
