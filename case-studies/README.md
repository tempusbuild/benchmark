# Case studies — real OSS projects

A **case study** benchmarks a *real* open-source project's **own** test command on both runners,
so the comparison cannot be dismissed as artificial. The single-variable rule holds: the two caller
workflows differ **only** in `runs-on:`. The upstream project's steps are unchanged.

## Fetched at pipeline time — nothing vendored

The upstream project's code is **not stored in this repo**. Each case-study run checks the project
out at a **pinned commit** at pipeline time and runs its own test command. What we commit is only:

- two thin caller workflows + one reusable workflow (e.g. `casestudy-flask*.yml`), and
- a pin record under [`projects/`](projects/) (upstream repo, commit, licence, command).

So there is no mirror repo and no third-party code in our git — only a workflow that says "check
out `pallets/flask@<sha>` and run `uv run --locked tox run -e py3.14`".

## How it works (flask example)

```text
.github/workflows/casestudy-flask.yml          reusable: checkout flask @pinned sha → its test cmd
        ├── casestudy-flask-tempus.yml          runner: tempus-ubuntu-24.04-4core
        └── casestudy-flask-github.yml          runner: ubuntu-latest

run both (workflow_dispatch) >=3x per runner
        │
        ▼  scripts/case_study_collect.py --repo <this-benchmark-repo> --ref <flask-sha> \
               --tempus-workflow casestudy-flask-tempus.yml --github-workflow casestudy-flask-github.yml
        ▼  median wall-clock per runner (from the GitHub API) → comparison row
```

`--repo` is the repo whose Actions runs are read (this benchmark repo, where the case-study
workflows live); `--ref` is the pinned **upstream** flask commit those runs measured.

## What stays honest

- **Only `runs-on:` differs.** The two callers are byte-identical apart from the `runner` input;
  the actual steps live once in the reusable workflow.
- **Shape-parity runners.** Both target the **4 vCPU / 16 GB** shape — `ubuntu-latest` (the
  public GitHub-hosted standard) and `tempus-ubuntu-24.04-4core` (provisioned to the same shape).
  Neither side gets more hardware; the upstream matrix is collapsed to one Linux / Python-3.14 leg
  so we race one identical job, not two different matrices. Non-Linux legs are not run (not the
  shape under comparison).
- **Point-in-time, not a moving target.** The commit is pinned in the workflow and the pin record,
  and every published number records that ref and the date. When upstream evolves, bump the pin
  deliberately and re-run.
- **Same fairness rules.** Median of at least three runs; cold and warm reported separately (no
  action-level cache is enabled, so the default is an honest cold path); 4 vCPU / 16 GB parity.

## Fork-PR safety

The case-study workflows are `workflow_dispatch` only — there is **no `pull_request` trigger**, so
no outside fork can run code on a self-hosted runner. They are run deliberately, not on every commit.

## Legal

A case study runs an upstream project's own command on its own pinned code. Pick projects under a
permissive licence, record the licence in the pin record, and credit the project. The numbers
describe how that project's tests run on each runner; they do not imply any endorsement by the
upstream project.

## Adding a project

Good candidates have a permissive licence, a test command that runs on `ubuntu-latest` without
secrets or external services, and a suite that completes in minutes on a single 4 vCPU leg. Copy
the three `casestudy-flask*.yml` workflows and [`projects/flask.yaml`](projects/flask.yaml), set
the upstream repo, the pinned commit, and the project's own one-leg test command.
