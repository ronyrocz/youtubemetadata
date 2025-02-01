.PHONY: help install venv run migrate lint test clean

# Default help message
help:
	@echo "Usage: make [target]"
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Create and activate virtual environment
venv: ## Set up virtual environment
	python -m venv venv
	@echo "Run 'source venv/bin/activate' to activate the virtual environment"

# Install dependencies
install: ## Install dependencies from requirements.txt
	pip install -r requirements.txt

# Run Django server
run: ## Run the Django development server
	python3 manage.py runserver

# Build database migrations
migrations: ## Build databamakese migrations
	python3 manage.py makemigrations videoservice

# Apply database migrations
migrate: ## Apply database migrations
	python3 manage.py migrate

# Linting with Black
lint: ## Check code formatting with Black
	black --check .

# Run tests
unit-test: ## Run Django tests
	pytest

stress-test: ## Stress test to find out latency using Locust
	 locust -f videoservice/stress_test/locust_stress_test.py --host=http://127.0.0.1:8000


# Clean up pyc and cache files
clean: ## Remove cache and temporary files
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -exec rm -rf {} +

run-celery: ## Run celery
	celery -A videoservice worker --loglevel=info

verify-celery-tasks: ## Verify active tasks on your local celery
	celery -A videoservice inspect registered
