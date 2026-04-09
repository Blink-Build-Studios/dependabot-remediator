.PHONY: install test lint migrate

# Install all dependencies (production + dev)
install:
	pip install -e ".[dev]"

# Run the full test suite
test:
	pytest tests/ -v

# Run linting and formatting checks
lint:
	ruff check .
	ruff format --check .

# Auto-fix lint and formatting issues
lint_fix:
	ruff check . --fix
	ruff format .

# Run database migrations
migrate:
	python manage.py migrate
