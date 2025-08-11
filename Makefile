# FFIEC Data Collector - Development Commands

.PHONY: help install install-dev test lint format type-check build clean docs serve-docs

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install package in development mode"
	@echo "  install-dev  - Install with development dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting (black + flake8)"
	@echo "  format       - Format code with black"
	@echo "  type-check   - Run mypy type checking"
	@echo "  build        - Build distribution packages"
	@echo "  clean        - Clean build artifacts"
	@echo "  docs         - Build documentation"
	@echo "  serve-docs   - Build and serve documentation locally"
	@echo "  check-all    - Run all checks (format, lint, type-check, test)"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testing
test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --tb=short --cov=ffiec_data_collector --cov-report=html

# Code quality
format:
	black ffiec_data_collector/ tests/

lint:
	black --check ffiec_data_collector/ tests/
	flake8 ffiec_data_collector/ tests/

type-check:
	mypy ffiec_data_collector/

# Build and packaging
build:
	python -m build

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Documentation
docs:
	cd docs && make html

serve-docs: docs
	cd docs/_build/html && python -m http.server 8000

# Combined checks
check-all: format lint type-check test
	@echo "✅ All checks passed!"

# PyPI publishing (manual)
publish-test:
	python -m twine upload --repository testpypi dist/*

publish:
	python -m twine upload dist/*