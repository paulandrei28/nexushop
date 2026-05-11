# NexuShop - Self-Healing Microservices E-Commerce Platform

A production-grade, event-driven e-commerce backend demonstrating microservices architecture, self-healing patterns, and full observability -- built with Python, Docker Compose, and CI/CD.

## Architecture

```mermaid
graph TB
    Client([Client / Angular Frontend])
    GW[API Gateway<br/>FastAPI + Redis]

    Client --> GW

    GW --> PS[Product Service<br/>Flask + PostgreSQL]
    GW --> OS[Order Service<br/>FastAPI + PostgreSQL]
    GW --> IS[Inventory Service<br/>Flask + PostgreSQL]

    OS -- order.created --> RMQ[(RabbitMQ)]
    RMQ -- inventory.reserve --> IS
    IS -- inventory.reserved --> RMQ
    RMQ -- order.confirmed --> OS
    RMQ -- notification.send --> NS[Notification Service<br/>FastAPI + Mailhog]

    PS --> PG[(PostgreSQL<br/>products_db)]
    OS --> PG2[(PostgreSQL<br/>orders_db)]
    IS --> PG3[(PostgreSQL<br/>inventory_db)]

    subgraph Observability
        PROM[Prometheus]
        GRAF[Grafana]
        JAEG[Jaeger]
    end

    PS -.-> PROM
    OS -.-> PROM
    IS -.-> PROM
    PROM --> GRAF
    PS -.-> JAEG
    OS -.-> JAEG
    IS -.-> JAEG
```

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| API Gateway | FastAPI + Redis | Routing, JWT auth, rate limiting |
| Product Service | Flask + PostgreSQL | Product catalog CRUD |
| Order Service | FastAPI + PostgreSQL | Order lifecycle, saga pattern |
| Inventory Service | Flask + PostgreSQL | Stock management |
| Notification Service | FastAPI | Event-driven email notifications |
| Messaging | RabbitMQ | Async event bus with dead letter queues |
| Caching | Redis | Rate limiting, response caching |
| Monitoring | Prometheus + Grafana | Metrics and dashboards |
| Tracing | OpenTelemetry + Jaeger | Distributed request tracing |
| CI/CD | GitHub Actions | Lint, test, build, integration tests |
| Load Testing | Locust | Performance benchmarking |

## Self-Healing Patterns

- **Circuit Breakers** (pybreaker) -- open after 5 failures, auto-reset after 30s
- **Retry with Exponential Backoff** (tenacity) -- transient failure recovery
- **Health Checks** -- `/health` and `/ready` endpoints on every service
- **Docker Healthchecks** -- automatic container restart on failure
- **Dead Letter Queues** -- failed messages captured for inspection
- **Graceful Degradation** -- cached responses when downstream services are unavailable

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Make (optional, for convenience commands)

### Run

```bash
# Start all services
make up
# or: docker compose up -d --build

# Check service health
make health

# View logs
make logs

# Seed sample products
make seed

# Run tests
make test

# Stop everything
make down

# Full cleanup (removes volumes)
make clean
```

### Service Endpoints

| Service | URL | Description |
|---|---|---|
| API Gateway | http://localhost:8000 | Unified entry point (JWT, rate limiting, circuit breakers) |
| Product Service | http://localhost:8001 | Product CRUD API |
| Order Service | http://localhost:8002 | Order lifecycle + saga orchestration |
| Inventory Service | http://localhost:8003 | Stock management + reservations |
| Notification Service | http://localhost:8004 | Event-driven email notifications |
| RabbitMQ Management | http://localhost:15672 | Message broker UI (guest/guest) |
| Mailhog | http://localhost:8025 | Email testing UI |

### API Examples

```bash
# --- Via API Gateway (port 8000) ---
# Browse products (public, no auth)
curl http://localhost:8000/products

# Get a JWT token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@nexushop.com"}'
# Response: {"access_token": "eyJ...", "token_type": "bearer"}

# Use token for protected endpoints
export TOKEN="eyJ..."

# Place an order (requires auth)
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"customer_email": "buyer@example.com", "items": [{"product_id": "<id>", "product_name": "Keyboard", "quantity": 2, "unit_price": 49.99}]}'

# Check circuit breaker status
curl http://localhost:8000/gateway/circuits

# Check your JWT claims
curl http://localhost:8000/auth/me -H "Authorization: Bearer $TOKEN"

# --- Direct Service Access ---
# List products
curl http://localhost:8001/products

# Create a product
curl -X POST http://localhost:8001/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Keyboard", "price": 49.99, "category": "Electronics"}'

# Get a product
curl http://localhost:8001/products/{id}

# Search products
curl "http://localhost:8001/products?search=keyboard&category=Electronics"

# Health check
curl http://localhost:8001/health
curl http://localhost:8001/ready

# --- Order Flow (Saga Pattern) ---
# 1. Set inventory for a product
curl -X POST http://localhost:8003/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_id": "<product-id>", "quantity": 50}'

# 2. Place an order (triggers saga: order -> reserve -> confirm -> notify)
curl -X POST http://localhost:8002/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_email": "buyer@example.com", "items": [{"product_id": "<product-id>", "product_name": "Keyboard", "quantity": 2, "unit_price": 49.99}]}'

# 3. Check order status (pending -> confirmed/failed)
curl http://localhost:8002/orders/<order-id>

# 4. Check emails sent (Mailhog UI)
# Open http://localhost:8025 in your browser
```

## Project Structure

```
.
├── docker-compose.yml          # Full stack orchestration
├── Makefile                    # Developer convenience commands
├── shared/                     # Shared libraries across services
│   ├── messaging.py            # RabbitMQ connection + helpers
│   ├── health.py               # Health check blueprint
│   ├── circuit_breaker.py      # Circuit breaker wrapper
│   └── logging_config.py       # Structured JSON logging
├── gateway/                    # API Gateway (FastAPI + Redis)
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py, auth.py, rate_limiter.py, service_proxy.py
│   └── tests/
├── product-service/            # Product catalog (Flask)
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py, models.py, routes.py, repository.py
│   └── tests/
├── order-service/              # Order lifecycle + saga (FastAPI)
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py, models.py, routes.py, events.py
│   └── tests/
├── inventory-service/          # Stock management (Flask)
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py, models.py, routes.py, events.py
│   └── tests/
├── notification-service/       # Email notifications (FastAPI)
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py, events.py, email_sender.py
│   └── tests/
├── scripts/
│   ├── init-databases.sql      # Creates per-service databases
│   └── seed_data.py            # Sample product data
└── .github/workflows/          # CI/CD pipelines (Phase 6)
```

## Development Roadmap

- [x] Phase 1: Foundation (infrastructure + Product Service)
- [x] Phase 2: Core Services (Order + Inventory + event-driven flow)
- [x] Phase 3: API Gateway + Self-Healing patterns
- [ ] Phase 4: Observability (Prometheus, Grafana, Jaeger)
- [ ] Phase 5: Angular Frontend
- [ ] Phase 6: CI/CD + Load Testing + Polish
