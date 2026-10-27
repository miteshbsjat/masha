.PHONY: format lint typecheck security test check clean

src_dirs = masha test

format:
	poetry run isort $(src_dirs)
	poetry run black $(src_dirs)
	poetry run ruff check --fix $(src_dirs)

lint:
	poetry run isort --check-only $(src_dirs)
	poetry run black --check $(src_dirs)
	poetry run ruff check $(src_dirs)

typecheck:
	poetry run mypy

security:
	poetry run bandit -q -c pyproject.toml -r masha
	poetry run pip-audit

test:
	poetry run pytest --cov=masha --cov-report=term-missing

check: lint typecheck security test

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage dist
