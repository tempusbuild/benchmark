# Results

This directory holds published benchmark measurements. **No number appears here unless it came
from an actual CI run** — see [`../methodology.md`](../methodology.md) for the rules (single
variable `runs-on:`, shape parity, median of at least three runs, cold vs warm cache reported
separately, upstream project pinned to a specific commit).

## How results are published

1. Both caller workflows for a case study are run at least three times each, for each cache
   state (cold and warm), using `workflow_dispatch`.
2. Wall-clock time is read from the GitHub API (`run_started_at` .. `updated_at`).
3. The runs are reduced to a **median** per (case study, runner, cache state):

   ```bash
   python scripts/case_study_collect.py \
       --repo tempusbuild/benchmark \
       --upstream django/django \
       --ref <upstream-commit-sha> \
       --tempus-workflow casestudy-django-tempus.yml \
       --github-workflow casestudy-django-github.yml
   ```

   This prints the Markdown rows that replace the table below.
4. The run count, upstream ref, cache state, and date are recorded with every row so a reader
   can judge and reproduce the number.

## Latest results

The table below is the template. It is intentionally empty — it will be populated only with
measured medians, never estimates. There is one row per (upstream project, runner, cache state).

| Upstream | Ref | Runner | Runs | Median wall-clock | Cache | Date |
| -------- | --- | ------ | ---- | ----------------- | ----- | ---- |
| `django/django` | — | `ubuntu-latest`             | — | — | cold | — |
| `django/django` | — | `tempus-ubuntu-24.04-4core` | — | — | cold | — |

(Warm-cache rows are added the same way, with `warm` in the Cache column. Cold and warm are never
blended in a single row.)

Column meanings:

- **Upstream** — the real OSS project whose own test command was run.
- **Ref** — the pinned upstream commit SHA the runs measured (first 7 chars shown).
- **Runner** — the `runs-on:` label.
- **Runs** — number of runs the median is taken over (at least three).
- **Median wall-clock** — median total measured wall-clock time across those runs.
- **Cache** — `cold` (no primed dependency cache) or `warm` (primed). Never blended.
- **Date** — date the runs were collected.
