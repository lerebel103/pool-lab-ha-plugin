.PHONY: lint format check test test-cov clean install ci validate

lint:
	ruff check custom_components/ tests/
	ruff format --check custom_components/ tests/

validate:
	python scripts/validate_manifest.py

format:
	ruff check --fix custom_components/ tests/
	ruff format custom_components/ tests/

check: lint validate

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ -v --cov=custom_components.pool_lab --cov-report=term-missing --cov-report=html

clean:
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

install:
	pip install -e ".[dev]"

ci: lint validate test
