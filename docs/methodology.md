# Benchmark methodology

This document describes how the tempus.build CI benchmarks are run so that the comparison is fair
and the numbers are reproducible. The whole point is that nobody has to trust a marketing claim:
the projects, the workflows, and the rules below are all public.

## Approach: real OSS projects, single variable

Each benchmark runs a real open-source project's **own** test command on both runners. The upstream
project's code is fetched at a pinned commit at pipeline time — no code is stored in this repo.
What lives here is only two thin caller workflows and the reusable workflow that defines the steps.

The single variable is `runs-on:`. For each case study there are three workflow files — two thin
callers plus one reusable workflow that holds the measured steps. The callers differ only in the
`runner` input they pass:

| Caller workflow              | `runs-on:`                  |
| ---------------------------- | --------------------------- |
| `casestudy-<name>-tempus.yml`  | `tempus-ubuntu-24.04-4core` |
| `casestudy-<name>-github.yml`  | `ubuntu-latest`             |

Both callers pass a `runner` input to a single reusable workflow that contains all measured steps.
Because the steps live in one place, they cannot drift apart — the only difference between a tempus
run and a github run is the `runner` input. There is no second copy of the steps.

## Shape parity

`ubuntu-latest` on a **public** repository is a 4 vCPU / 16 GB runner. The tempus.build label
used here, `tempus-ubuntu-24.04-4core`, is provisioned to the same shape: **4 vCPU / 16 GB**.
This is deliberately the standard public-runner size, not a premium tier — neither side is given
more hardware than the other, so a difference in wall-clock time reflects the runner, not the spec.

Both sides run Ubuntu 24.04 (`ubuntu-latest` currently maps to Ubuntu 24.04).

## What is measured

The upstream project's own test command runs without modification. Timing comes from the workflow
run's own start and end timestamps (`run_started_at` .. `updated_at`) via the GitHub API.
`scripts/case_study_collect.py` reads those timestamps, takes the median, and renders a comparison
row. Only measured runs are ever summarized — never estimates.

## Median of at least three runs

A single CI run is noisy (scheduling, network, neighbor load). Each reported number is the
**median of at least three runs** of the same workflow on the same runner. The median is used
rather than the mean so that a single outlier run does not dominate the result. The run count is
recorded alongside every published number.

## Cold cache vs warm cache

Dependency download and resolution dominates many CI runs, and caching changes the picture
substantially. Cold and warm runs are therefore reported **separately**, never blended:

- **Cold cache** — no pre-populated dependency cache; everything is fetched fresh. This is the
  worst case and the most honest baseline. The reusable workflow does not enable any action-level
  cache, so the default path is cold.
- **Warm cache** — dependencies are served from a primed cache. This reflects steady-state CI on
  a project that runs frequently. For tempus.build runners this means the colocated proxy has
  already been populated; for the GitHub side an equivalent primed state is set up by the operator.

A "speedup" claim must state which cache state it refers to. Comparing tempus warm against GitHub
cold (or vice versa) is not a valid comparison and is not published.

## Point-in-time, not a moving target

Each case study is pinned to a specific upstream commit. Published results record both the ref
and the date. As the upstream project evolves, the numbers for an older pin become historical
rather than current; update the pin and re-run rather than blending runs across different refs.

## What is controlled, and what isn't

**Controlled** (held identical across both runners):

- Workflow steps and their order (one reusable workflow called by both thin callers).
- Upstream project source (same pinned commit) and its own lockfile or pinned dependencies.
- Runner shape (4 vCPU / 16 GB).
- The single Linux / Python leg that is run (non-Linux legs and other matrix legs are excluded;
  we race one identical job per runner, not two different matrices).

**Not fully controlled** (inherent to comparing two different platforms — disclosed, not hidden):

- Network path and bandwidth to package registries differ between platforms; this is part of what
  the benchmark is measuring, and is the reason cold and warm runs are reported separately.
- Background load and scheduling on shared infrastructure on either side. The median-of-N rule is
  there to dampen this; it cannot eliminate it.
- Exact CPU model and storage backing the "4 vCPU / 16 GB" shape may differ between platforms.
  This is an intentional part of the comparison (it is what a customer actually gets), and the
  shape is matched on the dimensions GitHub publishes.

## Reproducing a run

1. Fork this repository.
2. Make a tempus.build runner available under the `tempus-ubuntu-24.04-4core` label (for the
   GitHub side, no setup is needed — `ubuntu-latest` is provided by GitHub).
3. Trigger both caller workflows for the case study you want
   (`workflow_dispatch` — there is no `pull_request` trigger on these workflows).
4. Repeat at least three times per runner for a stable median.
5. Reduce the results to a comparison row with `scripts/case_study_collect.py`
   (see [`results/README.md`](results/README.md)).

## Fork-PR safety

The case-study workflows use `workflow_dispatch` only — there is no `pull_request` trigger. A fork
PR cannot automatically execute code on a self-hosted runner. Runs are always deliberate, approved
actions.
