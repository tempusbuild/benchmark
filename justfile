# Common tasks for the benchmark repo. `just` with no argument lists recipes.
default:
    @just --list

# Install pre-commit hooks (run once after cloning).
hooks:
    uv sync
    pre-commit install

# Lint everything: ruff (check + format), actionlint, gitleaks.
lint:
    pre-commit run --all-files

# Run the harness unit tests.
test:
    uv run pytest scripts/

# Reduce the django case study's runs into a comparison row, e.g.:
#   just results-django c14b756185c88f7f2eb745ff061f3c221fea9de7
# One recipe per case study (the workflow filenames are study-specific).
results-django ref:
    uv run python scripts/case_study_collect.py \
        --repo tempusbuild/benchmark \
        --upstream django/django \
        --ref {{ ref }} \
        --tempus-workflow casestudy-django-tempus.yml \
        --github-workflow casestudy-django-github.yml
