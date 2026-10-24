.PHONY: install dev test lint clean examples help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install hulang (makes `nlc` available on PATH)
	pip install .

dev: ## Install in development mode with test/lint deps
	pip install -e ".[dev]"

test: ## Run unit tests (skips integration tests that call LLM)
	python -m pytest tests/ -m "not integration" -v

test-all: ## Run all tests including integration (requires API access)
	python -m pytest tests/ -v

lint: ## Run linter
	ruff check hulang/ tests/

lint-fix: ## Run linter with auto-fix
	ruff check --fix hulang/ tests/

clean: ## Remove build artifacts and compiled binaries
	rm -rf dist/ build/ *.egg-info __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

examples: ## Compile all example programs
	@for f in examples/*.txt; do \
		echo "\n━━━ Compiling $$f ━━━"; \
		python -m hulang.cli build "$$f" --emit-source -o "examples/$$(basename $$f .txt)" || true; \
	done
