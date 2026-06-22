# Security Policy

`tempusbuild/benchmark` is a public repository that runs real OSS projects' own test commands on
both GitHub-hosted runners and tempus.build self-hosted runners. Because self-hosted runners
execute the workflows in this repo, the way those workflows are triggered is itself a security
boundary. This document explains that boundary and how to report a vulnerability.

## Fork-PR policy

The case-study workflows that run on a **tempus.build self-hosted runner**
(`runs-on: tempus-ubuntu-24.04-4core`) do **not** run automatically on pull requests from forks.
They are triggered only by:

- manual `workflow_dispatch` by a maintainer.

There is intentionally no `pull_request` trigger on those workflows. This prevents an arbitrary
fork PR from executing untrusted code on our self-hosted runner without explicit maintainer action.

Even when a self-hosted runner does pick up a job, running it is gated by GitHub's standard
controls for self-hosted runners on public repositories: outside-collaborator workflow approval is
required before a workflow from an external contributor runs, and the runner is not exposed to
public repositories unless a maintainer enables it. Running untrusted code on our runners is always
an explicit, approved action — never automatic.

The repository's own linting workflow (`ci.yml`) runs on a GitHub-hosted runner
(`ubuntu-latest`) and is safe to run on pull requests; it never executes on a self-hosted runner.

## Reporting a vulnerability

If you find a vulnerability in this repository, its workflows, or the benchmark harness:

- Preferably — privately via **GitHub Security Advisories**: "Report a vulnerability" on the
  **Security** tab of this repository
  (`https://github.com/tempusbuild/benchmark/security/advisories/new`).
- Do not open a public issue for an unpatched vulnerability.

We will acknowledge receipt and keep you posted on triage and the fix.
