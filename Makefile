.PHONY: up down build logs test lint clean seed help

COMPOSE = docker compose

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
	$(COMPOSE) up -d --build

down: ## Stop all services
	$(COMPOSE) down

build: ## Build all images without starting
	$(COMPOSE) build

logs: ## Tail logs for all services
	$(COMPOSE) logs -f

logs-service: ## Tail logs for a specific service (usage: make logs-service SVC=product-service)
	$(COMPOSE) logs -f $(SVC)

restart: ## Restart a specific service (usage: make restart SVC=product-service)
	$(COMPOSE) restart $(SVC)

ps: ## Show running services
	$(COMPOSE) ps

test: ## Run all unit tests
	$(COMPOSE) exec product-service pytest tests/ -v

test-local: ## Run tests locally (no Docker)
	cd product-service && python -m pytest tests/ -v

lint: ## Run linters (black + flake8)
	black --check .
	flake8 --max-line-length=88 --extend-ignore=E203 .

format: ## Auto-format code with black
	black .

seed: ## Seed the database with sample data
	$(COMPOSE) exec product-service python -m scripts.seed_data

clean: ## Remove all containers, volumes, and images
	$(COMPOSE) down -v --rmi local

migrate: ## Run database migrations for a service (usage: make migrate SVC=product-service)
	$(COMPOSE) exec $(SVC) alembic upgrade head

health: ## Check health of all services
	@echo "Product Service:" && curl -s http://localhost:8001/health | python -m json.tool || echo "DOWN"
