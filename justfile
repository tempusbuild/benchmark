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

# Reduce the flask case study's runs into a comparison row, e.g.:
#   just results-flask pallets/flask 22d924701a6ae2e4cd01e9a15bbaf3946094af65
# One recipe per case study (the workflow filenames are study-specific).
results-flask repo ref:
    uv run python scripts/case_study_collect.py \
        --repo {{ repo }} \
        --ref {{ ref }} \
        --tempus-workflow casestudy-flask-tempus.yml \
        --github-workflow casestudy-flask-github.yml
