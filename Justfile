# Default: list available recipes
list:
    @just --list

# Install package in editable mode with dev dependencies
install:
    pip install -e ".[dev]" -i https://package-mirror.liara.ir/repository/pypi/simple

# Run all tests
test:
    pytest tests/

# Run specific tests matching a pattern
testf PATTERN:
    pytest tests/ -k "{{PATTERN}}" -v

# Run tests with coverage (terminal)
cov:
    pytest --cov=statewire --cov-report=term-missing tests/

# Run tests with HTML coverage report
cov-html:
    pytest --cov=statewire --cov-report=html tests/
    @echo "Open htmlcov/index.html to view report"

# Lint with ruff
lint:
    ruff check .

# Auto-fix lint issues
fix:
    ruff check --fix .

# Format with ruff
fmt:
    ruff format .

# Check formatting without applying
fmt-check:
    ruff format --check .

# Type check with mypy
typecheck:
    mypy

# Run lint + format check + typecheck
check: lint fmt-check typecheck

# Run lint + format + typecheck (auto-fix)
check-fix: fix fmt typecheck

# Clean build artifacts and cache
clean:
    rm -rf dist/ build/ htmlcov/ .coverage .pytest_cache .mypy_cache
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

# Build package (clean first)
build: clean
    python -m build
    twine check dist/*

# Publish to TestPyPI
publish-test:
    twine upload --repository testpypi dist/*

# Publish to PyPI (production)
publish:
    twine upload dist/*

# Full release: build + publish to both
release: build publish-test publish
