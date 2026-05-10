# ──────────────────────────────────────────────
# AI RAG Widget — Makefile
# ──────────────────────────────────────────────

PROJECT_NAME := ai-rag-widget
PYTHON       := python3
PYTEST       := $(PYTHON) -m pytest
RUFF         := $(PYTHON) -m ruff
UVICORN      := $(PYTHON) -m uvicorn

# ─── Help ─────────────────────────────────────

.PHONY: help
help:
	@echo "Usage:"
	@echo "  make install      — Install all dependencies"
	@echo "  make dev-install  — Install dev/test dependencies"
	@echo "  make lint         — Run ruff linter + formatter check"
	@echo "  make format       — Auto-format with ruff"
	@echo "  make test         — Run all tests (pytest)"
	@echo "  make test-v       — Run tests with verbose output"
	@echo "  make test-cov     — Run tests with coverage report"
	@echo "  make run          — Start development server"
	@echo "  make docker-build — Build Docker image"
	@echo "  make docker-up    — Start Docker Compose"
	@echo "  make docker-down  — Stop Docker Compose"
	@echo "  make clean        — Clean cache files"
	@echo "  make count-lines  — Count Python lines of code"

# ─── Install ──────────────────────────────────

.PHONY: install dev-install
install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	@echo "✅ Production dependencies installed"

dev-install: install
	$(PYTHON) -m pip install -r tests/requirements-test.txt
	$(PYTHON) -m pip install pytest-cov  # optional
	@echo "✅ Dev dependencies installed"

# ─── Lint / Format ────────────────────────────

.PHONY: lint format
lint:
	$(RUFF) check . --ignore E501
	@echo "✅ Lint passed"

format:
	$(RUFF) format .
	$(RUFF) check . --ignore E501 --fix
	@echo "✅ Formatted"

# ─── Test ─────────────────────────────────────

.PHONY: test test-v test-cov
test:
	$(PYTEST) tests/ -v --tb=short -x
	@echo "✅ All tests passed"

test-v:
	$(PYTEST) tests/ -v --tb=long -x --capture=no 2>&1 | head -200

test-cov:
	$(PYTEST) tests/ -v --tb=short --cov=. --cov-report=term-missing --cov-report=html
	@echo "✅ Coverage report: htmlcov/index.html"

# ─── Run ──────────────────────────────────────

.PHONY: run
run:
	PYTHONPATH=backend $(UVICORN) main:app --host 0.0.0.0 --port 8000 --reload

# ─── Docker ───────────────────────────────────

.PHONY: docker-build docker-up docker-down
docker-build:
	docker compose -f docker-compose.yml build

docker-up:
	docker compose -f docker-compose.yml up -d

docker-down:
	docker compose -f docker-compose.yml down

# ─── Clean ────────────────────────────────────

.PHONY: clean
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache htmlcov
	rm -rf chroma_db uploads
	@echo "✅ Cleaned"

# ─── Utilities ────────────────────────────────

.PHONY: count-lines
count-lines:
	@echo "Python source files (excl. tests and __pycache__):"
	find . -name '*.py' -not -path './__pycache__/*' \
	                  -not -path './*/__pycache__/*' \
	                  -not -path './.pytest_cache/*' \
	                  -not -path './chroma_db/*' \
	                  -not -path './uploads/*' | \
	xargs wc -l | tail -1
	@echo ""
	@echo "--- By directory ---"
	@find . -name '*.py' -not -path './__pycache__/*' \
	                  -not -path './*/__pycache__/*' \
	                  -not -path './.pytest_cache/*' \
	                  -not -path './chroma_db/*' \
	                  -not -path './uploads/*' | \
	xargs wc -l
