# =============================================================================
#  RetailStore — Makefile
#
#  Targets
#  -------
#  make build       Build all Docker images
#  make up          Start all services (foreground)
#  make up-d        Start all services (background)
#  make down        Stop all services
#  make down-v      Stop all services and delete volumes
#  make restart     Rebuild and restart everything
#  make logs        Tail logs for all services
#  make logs-<svc>  Tail logs for a specific service
#  make ps          Show running containers and health status
#  make shell-<svc> Open a shell inside a running service container
#  make test        Run tests for all services
#  make test-<svc>  Run tests for a specific service
#  make clean       Remove all stopped containers, unused images, volumes
# =============================================================================

COMPOSE  = docker compose
SVC_DIR  = retail-store/services

.DEFAULT_GOAL := help

.PHONY: help build up up-d down down-v restart logs ps clean \
        test test-catalog test-cart test-orders \
        shell-catalog shell-cart shell-orders shell-ui \
        migrate-catalog migrate-orders seed

# =============================================================================
# Help
# =============================================================================
help:
	@echo ""
	@echo "RetailStore — available make targets:"
	@echo ""
	@echo "  build            Build (or rebuild) all Docker images"
	@echo "  up               Start all services in the foreground"
	@echo "  up-d             Start all services in the background"
	@echo "  down             Stop all services"
	@echo "  down-v           Stop all services and remove data volumes"
	@echo "  restart          Rebuild images and restart all services"
	@echo "  logs             Tail logs for all services"
	@echo "  logs-catalog     Tail logs for the Catalog Service"
	@echo "  logs-cart        Tail logs for the Cart Service"
	@echo "  logs-orders      Tail logs for the Orders Service"
	@echo "  logs-ui          Tail logs for the UI Service"
	@echo "  logs-nginx       Tail logs for the Nginx proxy"
	@echo "  ps               Show container status and health"
	@echo "  shell-catalog    Open a shell inside the catalog-service container"
	@echo "  shell-cart       Open a shell inside the cart-service container"
	@echo "  shell-orders     Open a shell inside the orders-service container"
	@echo "  shell-ui         Open a shell inside the ui-service container"
	@echo "  test             Run tests for all services"
	@echo "  test-catalog     Run Catalog Service tests"
	@echo "  test-cart        Run Cart Service tests"
	@echo "  test-orders      Run Orders Service tests"
	@echo "  migrate-catalog  Run Catalog Service DB migrations"
	@echo "  migrate-orders   Run Orders Service DB migrations"
	@echo "  seed             Seed demo catalog data"
	@echo "  clean            Remove stopped containers, dangling images, volumes"
	@echo ""

# =============================================================================
# Docker Compose — core
# =============================================================================
build:
	$(COMPOSE) build

build-no-cache:
	$(COMPOSE) build --no-cache

up:
	$(COMPOSE) up

up-d:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

down-v:
	$(COMPOSE) down -v

restart: down build up-d

# =============================================================================
# Logs
# =============================================================================
logs:
	$(COMPOSE) logs -f

logs-catalog:
	$(COMPOSE) logs -f catalog-service

logs-cart:
	$(COMPOSE) logs -f cart-service

logs-orders:
	$(COMPOSE) logs -f orders-service

logs-ui:
	$(COMPOSE) logs -f ui-service

logs-nginx:
	$(COMPOSE) logs -f nginx

# =============================================================================
# Status
# =============================================================================
ps:
	$(COMPOSE) ps

# =============================================================================
# Shells
# =============================================================================
shell-catalog:
	$(COMPOSE) exec catalog-service /bin/bash

shell-cart:
	$(COMPOSE) exec cart-service /bin/bash

shell-orders:
	$(COMPOSE) exec orders-service /bin/bash

shell-ui:
	$(COMPOSE) exec ui-service /bin/bash

# =============================================================================
# Migrations (run inside running containers)
# =============================================================================
migrate-catalog:
	$(COMPOSE) exec catalog-service python manage.py migrate --noinput

migrate-orders:
	$(COMPOSE) exec orders-service python manage.py migrate --noinput

# =============================================================================
# Seeding
# =============================================================================
seed:
	$(COMPOSE) exec catalog-service python manage.py seed_catalog

# =============================================================================
# Tests (run locally, not inside containers — requires local venv per service)
# =============================================================================
test: test-catalog test-cart test-orders

test-catalog:
	@echo "--- Running Catalog Service tests ---"
	cd $(SVC_DIR)/catalog && pytest -v

test-cart:
	@echo "--- Running Cart Service tests ---"
	cd $(SVC_DIR)/cart && pytest -v

test-orders:
	@echo "--- Running Orders Service tests ---"
	cd $(SVC_DIR)/orders && pytest -v

# =============================================================================
# Cleanup
# =============================================================================
clean:
	docker system prune -f
	docker volume prune -f
	docker image prune -f
