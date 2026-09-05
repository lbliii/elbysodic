# Elbysodic Makefile
# Standard Python matches .python-version; override for free-threaded validation.

PYTHON_VERSION ?= 3.14.2
VENV_DIR ?= .venv

CHIRP_APP ?= elbysodic.web.contract_app:app
CONTRACT_DIFF_BASE ?= origin/main
CONTRACT_BASELINE ?= tests/fixtures/chirp_hypermedia_baseline.json

.PHONY: all help setup install test test-cov test-cov-parallel-safe test-cov-process lint lint-fix format format-check ty app-check kida-check milo-check contract-diff contract-baseline-check check ci changelog changelog-draft changelog-check build clean shell

all: help

help:
	@echo "Elbysodic Development CLI"
	@echo "========================="
	@echo "Python Version: $(PYTHON_VERSION)"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup           - Create virtual environment with Python $(PYTHON_VERSION)"
	@echo "  make install         - Install dependencies in development mode"
	@echo "  make test            - Run the test suite"
	@echo "  make test-cov        - Run parallel-safe and process tests with combined coverage"
	@echo "  make lint            - Run ruff linter"
	@echo "  make lint-fix        - Run ruff linter with auto-fix"
	@echo "  make format          - Run ruff formatter"
	@echo "  make format-check    - Check ruff formatting"
	@echo "  make ty              - Run ty type checker"
	@echo "  make app-check       - Run Chirp route/template check"
	@echo "  make kida-check      - Run kida static template validation"
	@echo "  make milo-check      - Verify the typed CLI and MCP contracts"
	@echo "  make contract-diff   - Diff hypermedia contracts vs $(CONTRACT_DIFF_BASE)"
	@echo "  make contract-baseline-check - Verify committed contract JSON baseline"
	@echo "  make check           - Run lint, format, types, strict app, Kida, contract baseline, and client tests"
	@echo "  make ci              - Run the full local gate (includes contract-diff)"
	@echo "  make changelog       - Compile changelog.d fragments into CHANGELOG.md"
	@echo "  make changelog-draft - Preview changelog from fragments"
	@echo "  make build           - Build distribution packages"
	@echo "  make clean           - Remove venv, build artifacts, and caches"
	@echo "  make shell           - Start a shell with the environment activated"

setup:
	@echo "Creating virtual environment with Python $(PYTHON_VERSION)..."
	uv venv --python $(PYTHON_VERSION) $(VENV_DIR)

install:
	@echo "Installing dependencies..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Error: $(VENV_DIR) not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@bash -c 'source "$(VENV_DIR)/bin/activate" && uv sync --active --group dev --frozen'

test:
	uv run pytest -q --tb=short

test-cov: test-cov-parallel-safe test-cov-process

test-cov-parallel-safe:
	uv run pytest -n auto -m "not process" --cov=elbysodic --cov-report= --cov-fail-under=0 --durations=20

test-cov-process:
	uv run pytest -m process --cov=elbysodic --cov-append --cov-report=term-missing --durations=20

lint:
	@echo "Running ruff linter..."
	uv run ruff check .

lint-fix:
	@echo "Running ruff linter with auto-fix..."
	uv run ruff check . --fix

format:
	@echo "Running ruff formatter..."
	uv run ruff format .

format-check:
	@echo "Checking ruff formatting..."
	uv run ruff format --check .

ty:
	@echo "Running ty type checker..."
	uv run ty check src/elbysodic/ tests/

app-check:
	uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check(warnings_as_errors=True)"

kida-check:
	uv run python scripts/kida_check.py

contract-diff:
	uv run chirp diff $(CHIRP_APP) --base $(CONTRACT_DIFF_BASE)

contract-baseline-check:
	uv run chirp check $(CHIRP_APP) --baseline $(CONTRACT_BASELINE)

milo-check:
	uv run milo verify src/elbysodic/cli.py

check:
	uv run python -m elbysodic.checks

ci:
	uv run python -m elbysodic.checks --full --base $(CONTRACT_DIFF_BASE)

changelog:
	uv run towncrier build --yes

changelog-draft:
	uv run towncrier build --draft

changelog-check:
	uv run towncrier check --compare-with origin/main

build:
	@echo "Building distribution packages..."
	rm -rf dist/
	uv build
	@echo "Built:"
	@ls -la dist/

clean:
	rm -rf $(VENV_DIR)
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ty_cache" -exec rm -rf {} + 2>/dev/null || true

shell:
	@echo "Activating environment..."
	@bash -c 'source $(VENV_DIR)/bin/activate && echo "venv active" && exec bash'
