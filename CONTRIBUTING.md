# Contributing

Thanks for your interest in improving the tempus.build CI benchmarks. The value of this repo is
its **fairness and reproducibility**, so contributions are held to that bar: a change must keep
the two case-study caller workflows identical apart from the `runner` input, and must not bias
the comparison.

## License of contributions and sign-off (DCO)

Contributions are accepted under the repository license, [Apache-2.0](LICENSE). By submitting a
PR you certify the [Developer Certificate of Origin](https://developercertificate.org/); sign off
each commit (`git commit -s`, adds a `Signed-off-by:` trailer). No CLA is required.

## Development setup

Requires [`uv`](https://docs.astral.sh/uv/), [`just`](https://github.com/casey/just), and
[`pre-commit`](https://pre-commit.com/). After cloning:

```bash
uv sync         # install pinned deps from uv.lock
just hooks      # install the pre-commit git hook
```

## Checks (run before opening a PR)

```bash
just lint       # ruff (check + format), actionlint, gitleaks — same set as CI
just test       # harness unit tests (scripts/)
```

The same set runs in `ci.yml`. PRs must be green.

## Conventions

- **Fairness first.** The two caller workflows for each case study (`casestudy-<name>-tempus.yml`
  and `casestudy-<name>-github.yml`) must differ *only* in the `runner` input. Any other
  divergence (extra caching, different step order) invalidates the comparison and will not be
  merged.
- **Pin everything.** GitHub Actions are pinned by commit SHA. Never `:latest` or floating tags.
- **No fabricated numbers.** Only results produced by an actual CI run belong in `docs/results/`.
  Each entry records the run count, the upstream ref, the cache state (cold/warm), and the date.
- **Comments** are English, written only where they add non-obvious context — no decorative
  banners, no restating the obvious.
- **Shell scripts** start with `set -euo pipefail`.

## Reporting security issues

Do not open a public issue for a vulnerability — see [`SECURITY.md`](SECURITY.md).
