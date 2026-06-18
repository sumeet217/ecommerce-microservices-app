# 🛒 RetailStore — Django Microservices E-Commerce

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.0-092E20?logo=django&logoColor=white)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/Django_REST_Framework-3.15-red)](https://www.django-rest-framework.org)
[![JWT](https://img.shields.io/badge/SimpleJWT-5.3-orange)](https://django-rest-framework-simplejwt.readthedocs.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![Nginx](https://img.shields.io/badge/Nginx-1.27-009639?logo=nginx&logoColor=white)](https://nginx.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A production-ready e-commerce backend built as a suite of independent Django microservices. Each service owns its own data store, exposes a REST API, and can be deployed, scaled, and tested in isolation.

---

## 📐 Architecture

```
                     ┌─────────────────────────────────┐
                     │       Browser / Mobile Client    │
                     └──────────────┬──────────────────┘
                                    │ :80
                     ┌──────────────▼──────────────────┐
                     │           Nginx Proxy            │
                     │   (API routing + static files)   │
                     └───┬─────┬────────┬────────┬─────┘
                         │     │        │        │
              /auth/  /catalog/ /cart/ /orders/  /  (UI)
                         │     │        │        │
           ┌─────────────▼┐  ┌─▼──────┐ │  ┌────▼────────────┐
           │ Auth Service │  │Catalog │ │  │  Orders Service  │
           │    :8004     │  │ :8001  │ │  │      :8003       │
           │ Django+JWT   │  │DRF+PG  │ │  │  Django REST+PG  │
           └──────┬───────┘  └───┬────┘ │  └────────────────┬┘
                  │              │    ┌──▼────┐              │
           ┌──────▼──────┐  ┌───▼──┐ │ Cart  │      ┌───────▼───┐
           │   auth-db   │  │cat-db│ │ :8002 │      │ orders-db │
           │  Postgres   │  │  PG  │ │DRF+   │      │ Postgres  │
           └─────────────┘  └──────┘ │Redis  │      └───────────┘
                                     └───┬───┘
                                     ┌───▼───┐
                                     │ Redis │
                                     │ :6379 │
                                     └───────┘
                     ┌──────────────────────────────────┐
                     │           UI Service             │
                     │  Django Templates + Bootstrap 5  │
                     │  (BFF — Backend for Frontend)    │
                     │           :8080                  │
                     └──────────────────────────────────┘
```

> The UI Service is the only service exposed to the browser. It acts as a BFF, calling backend APIs over the internal Docker network.

---

## 🧩 Services Overview

| Service | Port | Database | Responsibility |
|---|---|---|---|
| **Auth Service** | 8004 | PostgreSQL | User registration, JWT authentication, token management |
| **Catalog Service** | 8001 | PostgreSQL | Products, categories, search, inventory |
| **Cart Service** | 8002 | Redis | Session-based shopping cart |
| **Orders Service** | 8003 | PostgreSQL | Order placement, status lifecycle |
| **UI Service** | 80 / 8080 | — | Server-rendered storefront (Django Templates + Bootstrap 5) |

### Auth Service *(New)*
Handles all user identity and authentication for the platform. Provides JWT-based login with 15-minute access tokens and 7-day refresh tokens. Token blacklisting on logout prevents reuse. Exposes a `/verify/` endpoint that other microservices can call to validate tokens without sharing the secret key directly. Rate-limits the login endpoint to prevent brute-force attacks.

### Catalog Service
Manages the product catalogue — products, categories, images, and flexible attributes. Supports full-text search, category filtering, featured product listing, and auto-marks items `out_of_stock` when inventory hits zero.

### Cart Service
Stateless from the app layer — all cart state lives in Redis. Validates product availability against Catalog before adding. Enforces a max of 50 items and 99 units per item. Carts expire after 7 days. Identified via `X-Session-Key` header.

### Orders Service
Places orders by pulling live cart data, then freezes prices as immutable line items. Enforces a strict status machine: `PENDING → CONFIRMED → SHIPPED → DELIVERED`. Customers can cancel `PENDING` or `CONFIRMED` orders.

### UI Service
Six-page Django app: Home, Product Listing, Product Detail, Cart, Checkout, Order History & Detail. No database — uses signed-cookie sessions. Nginx serves static files; Gunicorn handles Django requests; Supervisord manages both in a single container.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Web Framework | Django 5.0, Django REST Framework 3.15 |
| Authentication | djangorestframework-simplejwt 5.3 (JWT + token blacklisting) |
| WSGI Server | Gunicorn 22 |
| Reverse Proxy | Nginx 1.27 |
| Process Manager | Supervisord |
| Relational DB | PostgreSQL 16 |
| Cache / Cart Store | Redis 7 |
| API Schema | drf-spectacular (OpenAPI 3) |
| Config Management | python-decouple |
| Testing | pytest, pytest-django, factory-boy, Faker |
| Containerisation | Docker, multi-stage Dockerfile per service |

---

## 🚀 Local Setup (Docker Compose)

### Prerequisites

- Docker 24+ and Docker Compose v2

### 1. Clone the repository

```bash
git clone https://github.com/sumeet217/ecommerce-microservices-app.git
cd ecommerce-microservices-app
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set all DJANGO_SECRET_KEY, DB passwords, and JWT settings
```

### 3. Build and start all services

```bash
docker compose up --build -d
```

### 4. Access the app

| URL | Description |
|---|---|
| http://localhost | Storefront |
| http://localhost:8080 | Direct UI (bypasses Nginx) |
| http://localhost:8004 | Auth Service (direct) |
| http://localhost/api/docs/auth/ | Auth API docs (Swagger) |
| http://localhost/api/docs/catalog/ | Catalog API docs (Swagger) |
| http://localhost/api/docs/cart/ | Cart API docs (Swagger) |
| http://localhost/api/docs/orders/ | Orders API docs (Swagger) |

### Useful commands

```bash
# View logs for all services
docker compose logs -f

# View logs for a specific service
docker compose logs -f auth-service

# Stop all services
docker compose down

# Fresh start (removes volumes / databases)
docker compose down -v

# Restart a single service
docker compose restart auth-service

# Run migrations manually
docker compose exec auth-service python manage.py migrate
```

---

## 🐳 DockerHub Images

Pre-built images are available on Docker Hub:

| Service | Image |
|---|---|
| Catalog Service | [`sumeet217/retailstore-catalog`](https://hub.docker.com/r/sumeet217/retailstore-catalog) |
| Cart Service | [`sumeet217/retailstore-cart`](https://hub.docker.com/r/sumeet217/retailstore-cart) |
| Orders Service | [`sumeet217/retailstore-orders`](https://hub.docker.com/r/sumeet217/retailstore-orders) |
| UI Service | [`sumeet217/retailstore-ui`](https://hub.docker.com/r/sumeet217/retailstore-ui) |

> **Auth Service** is built locally from `./retail-store/services/auth` via `docker compose up --build`.

---

## 📡 API Endpoints

### Auth Service — `http://localhost:8004`

```
POST /api/v1/auth/register/   Register a new user (returns JWT tokens)
POST /api/v1/auth/login/      Login with email + password (rate-limited: 10/min)
POST /api/v1/auth/refresh/    Exchange refresh token for a new access token
POST /api/v1/auth/logout/     Blacklist the refresh token (invalidate session)
GET  /api/v1/auth/me/         Get current user profile (requires JWT)
PATCH /api/v1/auth/me/        Update first_name, last_name, email (requires JWT)
POST /api/v1/auth/verify/     Validate a JWT token (for inter-service use)
GET  /health/                 Health check
```

**Authentication flow:**
```
Register/Login  →  { access_token, refresh_token }
                        │
    access_token ────►  Bearer <token> header on protected requests
    refresh_token ───►  POST /refresh/ to get a new access_token
                        POST /logout/  to blacklist the refresh_token
```

**JWT token lifetimes:**
| Token | Lifetime |
|---|---|
| Access token | 15 minutes |
| Refresh token | 7 days |

### Catalog Service — `http://localhost:8001`

```
GET  /api/v1/catalog/products/           List products (paginated, filterable)
GET  /api/v1/catalog/products/<id>/      Retrieve a product
GET  /api/v1/catalog/products/featured/  Featured products
GET  /api/v1/catalog/products/search/?q= Full-text search
GET  /api/v1/catalog/categories/         List categories
GET  /api/v1/catalog/categories/<id>/    Retrieve a category
GET  /health/                            Health check
```

### Cart Service — `http://localhost:8002`
> All endpoints require `X-Session-Key: <key>` header.

```
GET    /api/v1/cart/         Retrieve cart for session
POST   /api/v1/cart/add/     Add a product to cart
PUT    /api/v1/cart/update/  Update item quantity
DELETE /api/v1/cart/remove/  Remove a single item
DELETE /api/v1/cart/clear/   Clear entire cart
GET    /health/              Health check
```

### Orders Service — `http://localhost:8003`
> All endpoints require `X-User-Id: <id>` header.

```
GET  /api/v1/orders/             List orders for user (paginated)
POST /api/v1/orders/place/       Place order from current cart
GET  /api/v1/orders/<id>/        Retrieve a single order
PUT  /api/v1/orders/<id>/cancel/ Cancel an order
GET  /health/                    Health check
```

### Order Status Machine

```
PENDING ──► CONFIRMED ──► SHIPPED ──► DELIVERED
   │              │
   └──► CANCELLED ◄┘
```

---

## 🔐 Security

| Feature | Implementation |
|---|---|
| Password hashing | PBKDF2 (Django default) |
| JWT algorithm | HS256 |
| Token blacklisting | `rest_framework_simplejwt.token_blacklist` |
| Login rate limiting | 10 requests/minute (ScopedRateThrottle) |
| UUID user IDs | Prevents sequential enumeration |
| Email normalisation | Case-insensitive, lowercased on register & login |
| CORS | Configurable per-service via `CORS_ALLOWED_ORIGINS` |

---

## 📸 Screenshots

> Add screenshots by placing images in a `docs/screenshots/` folder and updating the paths below.

| Page | Preview |
|---|---|
| Home / Featured Products | ![Home](docs/screenshots/home.png) |
| Product Listing | ![Listing](docs/screenshots/listing.png) |
| Product Detail | ![Detail](docs/screenshots/detail.png) |
| Cart | ![Cart](docs/screenshots/cart.png) |
| Checkout | ![Checkout](docs/screenshots/checkout.png) |
| Order History | ![Orders](docs/screenshots/orders.png) |

---

## 🧪 Running Tests

Each service has an independent test suite using pytest, factory-boy, and Faker. Tests run against SQLite in-memory — no real database required.

```bash
# Auth Service (35+ test cases)
cd retail-store/services/auth    && pytest

# Catalog Service
cd retail-store/services/catalog && pytest

# Cart Service (uses fakeredis — no Redis needed)
cd retail-store/services/cart    && pytest

# Orders Service
cd retail-store/services/orders  && pytest
```

---

## 👤 Author

**Sumeet Mankari**
- GitHub: [@sumeet217](https://github.com/sumeet217)
- Project: [ecommerce-microservices-app](https://github.com/sumeet217/ecommerce-microservices-app)

---

## 📄 License

This project is licensed under the MIT License.
