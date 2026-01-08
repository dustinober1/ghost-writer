.PHONY: help build up down restart restart-clean restart-all logs clean seed migrate

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

up-logs: ## Start all services and show logs
	docker-compose up

down: ## Stop all services
	docker-compose down

restart: ## Restart all services (quick, keeps volumes and images)
	./restart_container.sh

restart-clean: ## Restart and remove volumes (database will be reset)
	./restart_container.sh -v

restart-all: ## Complete clean restart (removes volumes and images)
	./restart_container.sh -a

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

logs-db: ## Show database logs
	docker-compose logs -f postgres

clean: ## Stop and remove all containers, networks, and volumes
	docker-compose down -v
	docker system prune -f

seed: ## Create default demo user
	docker-compose exec backend python scripts/seed_default_user.py

migrate: ## Run database migrations
	docker-compose exec backend alembic upgrade head

shell-backend: ## Open shell in backend container
	docker-compose exec backend bash

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U ghostwriter -d ghostwriter

test: ## Run backend tests
	docker-compose exec backend pytest

rebuild: ## Rebuild all images from scratch
	docker-compose build --no-cache

prod: ## Start in production mode
	docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Stop production services
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## Show production logs
	docker-compose -f docker-compose.prod.yml logs -f

status: ## Show status of all services
	docker-compose ps
