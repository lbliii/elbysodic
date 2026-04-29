# Elbysodic Makefile
# Wraps uv commands to ensure Python 3.14t is used.

PYTHON_VERSION ?= 3.14t
VENV_DIR ?= .venv

.PHONY: all help setup install test test-cov lint lint-fix format format-check ty app-check check ci changelog changelog-draft changelog-check build clean shell

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
	@echo "  make test-cov        - Run tests with coverage report"
	@echo "  make lint            - Run ruff linter"
	@echo "  make lint-fix        - Run ruff linter with auto-fix"
	@echo "  make format          - Run ruff formatter"
	@echo "  make format-check    - Check ruff formatting"
	@echo "  make ty              - Run ty type checker"
	@echo "  make app-check       - Run Chirp route/template check"
	@echo "  make check           - Run lint, format-check, ty, and app-check"
	@echo "  make ci              - Run the full local gate"
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

test-cov:
	uv run pytest --cov=elbysodic --cov-report=term-missing

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
	uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"

check: lint format-check ty app-check

ci: check test

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
	@echo "Activating environment with GIL disabled..."
	@bash -c 'source $(VENV_DIR)/bin/activate && export PYTHON_GIL=0 && echo "venv active, GIL disabled" && exec bash'
