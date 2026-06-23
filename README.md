# benchmark

Public CI benchmarks comparing [tempus.build](https://tempus.build) self-hosted GitHub Actions
runners against GitHub-hosted runners.

The approach is real OSS, single variable: each benchmark takes a real open-source project's
**own** test command, runs it on both runners with the only difference being `runs-on:`, and
reports the median wall-clock time. The upstream project's code is fetched at a pinned commit at
pipeline time — nothing is vendored into this repo. The results, the methodology, and the
workflows are all public so anyone can reproduce or challenge them.

## How it works

For each case study there are three workflow files:

```
.github/workflows/casestudy-<name>.yml          reusable: checkout upstream @pinned → its test cmd
        ├── casestudy-<name>-tempus.yml          runner: tempus-ubuntu-24.04-4core
        └── casestudy-<name>-github.yml          runner: ubuntu-latest
```

Both caller workflows are identical apart from the `runner` input they pass. The measured steps
live once in the reusable workflow and cannot drift apart. Trigger both (`workflow_dispatch`) at
least three times, then reduce to a comparison row with `scripts/case_study_collect.py`.

## Shape parity

Both sides target the **4 vCPU / 16 GB** shape — the standard GitHub-hosted runner for public
repositories. Neither side gets more hardware. Wall-clock time difference reflects the runner,
not the spec.

## Case studies

| Upstream | Pinned ref | Test command |
| -------- | ---------- | ------------ |
| [django/django](https://github.com/django/django) | v6.0.6 (`ee93f65`) | `python tests/runtests.py --parallel` |

Pin records and runner details live in [`case-studies/projects/`](case-studies/projects/). To add
a project, see [`case-studies/README.md`](case-studies/README.md).

## Reproduce

```bash
# run both caller workflows via workflow_dispatch (>=3x per runner), then:
python scripts/case_study_collect.py \
    --repo tempusbuild/benchmark \
    --upstream django/django \
    --ref ee93f65169c280c9ab3d2ce103dd478c96d05065 \
    --tempus-workflow casestudy-django-tempus.yml \
    --github-workflow casestudy-django-github.yml
```

## Methodology and results

- **Methodology** — [`docs/methodology.md`](docs/methodology.md): what is controlled, what isn't,
  shape parity, the median-of-N rule, cold vs warm cache, and how timing is collected.
- **Results** — [`docs/results/`](docs/results/): published measurements and how they are produced.

## Contributing

Setup, checks, and sign-off — [`CONTRIBUTING.md`](CONTRIBUTING.md);
community rules — [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
Security and the fork-PR policy — [`SECURITY.md`](SECURITY.md).

## License

[Apache-2.0](LICENSE). The **tempus.build** name and logo are trademarks of tempus.build and are
not covered by the license.
