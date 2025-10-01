# Makefile for Parking project

.PHONY: help install test lint format coverage clean dev

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	poetry install

test: ## Run tests
	poetry run pytest -v

test-cov: ## Run tests with coverage
	poetry run pytest --cov=parking --cov-report=term-missing --cov-report=html

lint: ## Check code with linters
	poetry run ruff check .
	poetry run black --check .
	poetry run isort --check-only .
	poetry run mypy parking/

lint-fix: ## Fix linting issues automatically
	poetry run ruff check --fix .
	poetry run black .
	poetry run isort .

format: ## Format code
	poetry run black .
	poetry run isort .

coverage: test-cov ## Create coverage report
	@echo "Coverage report created in htmlcov/index.html"
	@echo "Open with: open htmlcov/index.html"

clean: ## Clean caches and temporary files
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/
	rm -rf .mypy_cache/

dev: ## Start development environment
	docker-compose -f docker-compose.dev.yml up -d

dev-stop: ## Stop development environment  
	docker-compose -f docker-compose.dev.yml down

dev-logs: ## Show development environment logs
	docker-compose -f docker-compose.dev.yml logs -f

# Testing commands
test-unit: ## Run only unit tests
	poetry run pytest tests/test_domain_models.py tests/test_use_cases.py tests/test_config.py -v

test-integration: ## Run integration tests
	poetry run pytest tests/test_http_server.py -v

# Database commands
db-test-data: ## Load test data
	docker-compose -f docker-compose.dev.yml exec parking python -c "from parking.application.config import ServiceConfig; from parking.infrastructure.mongodb_storage import MongoDBStorage; import asyncio; async def clear_db(): config = ServiceConfig(); storage = await MongoDBStorage.connect(config.mongodb); await storage._collection.delete_many({}); await storage.close(); print('Test data cleared'); asyncio.run(clear_db())"

# CI/CD commands
ci-test: install lint test-cov ## Run all CI checks
	@echo "All CI checks passed!"

# Docker commands  
docker-build: ## Build Docker image
	docker build -t parking:latest .

docker-run: ## Run in Docker
	docker run --rm -p 3847:3847 parking:latest

