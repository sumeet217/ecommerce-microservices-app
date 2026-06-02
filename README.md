# RetailStore — Django Microservices E-Commerce

A production-ready e-commerce backend built as a suite of independent Django microservices. Each service owns its own data store, exposes a REST API, and can be deployed, scaled, and tested in isolation.

---

## Table of Contents

- [Architecture](#architecture)
- [Services](#services)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Data Models](#data-models)
- [Running Tests](#running-tests)
- [Docker](#docker)
- [Service Communication](#service-communication)
- [Contributing](#contributing)

---

## Architecture

```
                        Browser / Mobile Client
                                |
                         [ UI Service :80 ]
                         Nginx + Gunicorn
                         Django Templates
                                |
              ┌─────────────────┼──────────────────┐
              |                 |                  |
   [ Catalog Service :8001 ]   [ Cart Service :8002 ]   [ Orders Service :8003 ]
     Django REST + PostgreSQL    Django REST + Redis      Django REST + PostgreSQL
```

All four services run in separate containers. The UI Service is the only service reachable from the browser; it acts as a backend-for-frontend (BFF) by calling the three backend APIs over the internal Docker network.

---

## Services

### Catalog Service (port 8001)

Manages the product catalogue. Owns all product, category, and image data.

- Products with pricing, inventory, images, and flexible attributes
- Category hierarchy
- Full-text search and filter endpoints
- Featured product list for the storefront homepage
- Auto-sets status to `out_of_stock` when inventory reaches zero

### Cart Service (port 8002)

Manages per-session shopping carts. Stateless from the application layer's perspective — all state lives in Redis.

- Add, update, remove, and clear cart items
- Validates product existence and availability against the Catalog Service before adding
- Enforces maximum item count (50) and maximum quantity per item (99)
- Cart data expires after 7 days of inactivity
- Identified by a session key passed in the `X-Session-Key` request header

### Orders Service (port 8003)

Handles order placement and lifecycle management. Reads cart contents from the Cart Service at placement time and freezes prices as immutable line items.

- Places orders by pulling cart contents from the Cart Service
- Enforces a strict status machine: `PENDING` → `CONFIRMED` → `SHIPPED` → `DELIVERED`
- Customer-initiated cancellation allowed for `PENDING` and `CONFIRMED` orders
- Shipping address and order notes captured at placement time
- Prices frozen at order time — future catalogue price changes do not affect historical orders

### UI Service (port 80)

A server-rendered Django application. Talks to the three backend services via HTTP and renders Bootstrap 5 templates.

- Six pages: Home, Product Listing, Product Detail, Cart, Checkout, Order History and Detail
- No database — uses signed-cookie sessions
- Nginx serves static files directly; Gunicorn handles all Django requests
- Supervisord manages both Nginx and Gunicorn inside a single container

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Web framework | Django 5.0, Django REST Framework 3.15 |
| WSGI server | Gunicorn 22 |
| Reverse proxy / static | Nginx |
| Process manager | Supervisord |
| Relational database | PostgreSQL 16 (Catalog, Orders) |
| Cache / Cart store | Redis 7 (Cart) |
| ORM | Django ORM |
| API schema | drf-spectacular (OpenAPI 3) |
| Environment config | python-decouple |
| Testing | pytest, pytest-django, factory-boy, Faker |
| Containerisation | Docker, multi-stage Dockerfile per service |

---

## Project Structure

```
retail-store/
  services/
    catalog/                  Catalog Service
      apps/
        categories/           Category model and API
        products/             Product, ProductImage, ProductAttribute models and API
      catalog_service/        Django settings, URLs, WSGI
      tests/
      Dockerfile
      requirements.txt
      .env.example

    cart/                     Cart Service
      apps/
        cart/                 CartRepository (Redis), CartItem, views
      cart_service/           Django settings, URLs, WSGI
      tests/
      Dockerfile
      requirements.txt
      .env.example

    orders/                   Orders Service
      apps/
        orders/               Order, OrderItem models, status machine, cart client
      orders_service/         Django settings, URLs, WSGI
      tests/
      Dockerfile
      requirements.txt
      .env.example

    ui/                       UI Service
      apps/
        store/
          templatetags/       Custom Django template filters
          views.py            Class-based views for all pages
          services.py         HTTP client layer for all backend calls
          context_processors.py
      ui_service/             Django settings, URLs, WSGI
      templates/store/        Django HTML templates (Bootstrap 5)
      static/
        css/store.css         Full custom design system
        js/store.js           Client-side interactions
      nginx/nginx.conf        Static serving and proxy configuration
      Dockerfile
      requirements.txt
      .env.example
```

---

## Prerequisites

- Docker 24+ and Docker Compose v2
- Python 3.12+ (for running services locally without Docker)
- PostgreSQL 16+ (for Catalog and Orders services, local setup)
- Redis 7+ (for Cart service, local setup)

---

## Getting Started

### Option A — Run all services with Docker Compose

A `docker-compose.yml` file is placed at the repository root. Each service image is built from its own multi-stage Dockerfile.

**Important:** Django migrations are included in the repository. If you need to regenerate them, delete the `migrations` folders and run `makemigrations` locally or in a container.

```bash
# Build and start all services
docker compose up --build -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Stop and remove volumes (fresh start)
docker compose down -v
```

Access the storefront at `http://localhost`.

**Available URLs:**
- Storefront: http://localhost
- Direct UI: http://localhost:8080
- Catalog API docs: http://localhost/api/docs/catalog/
- Cart API docs: http://localhost/api/docs/cart/
- Orders API docs: http://localhost/api/docs/orders/

### Option B — Run a single service locally

Each service is a standard Django project that can be run with the Django development server.

```bash
cd retail-store/services/catalog

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment variables
cp .env.example .env

# Run database migrations (Catalog and Orders only)
python manage.py migrate

# Start the development server
python manage.py runserver 8001
```

Repeat for each service, substituting the directory and port number (`8001` for Catalog, `8002` for Cart, `8003` for Orders, any free port for UI).

---

## Environment Variables

Every service reads its configuration exclusively from environment variables. A documented `.env.example` file lives at the root of each service directory.

### Catalog Service

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | — | Django secret key. Required. |
| `DJANGO_DEBUG` | `False` | Enable debug mode. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts. |
| `DATABASE_URL` | — | Full PostgreSQL connection string. Takes precedence over individual DB vars. |
| `DB_HOST` | `catalog-db` | PostgreSQL host. |
| `DB_PORT` | `5432` | PostgreSQL port. |
| `DB_NAME` | `catalog_db` | Database name. |
| `DB_USER` | `catalog_user` | Database user. |
| `DB_PASSWORD` | — | Database password. |
| `PAGE_SIZE` | `20` | Default API page size. |
| `LOG_LEVEL` | `INFO` | Logging level. |
| `CORS_ALLOWED_ORIGINS` | — | Comma-separated allowed CORS origins. |

### Cart Service

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | — | Required. |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string. |
| `CATALOG_SERVICE_URL` | `http://catalog-service:8001` | Internal URL of the Catalog Service. |
| `CATALOG_SERVICE_TIMEOUT` | `5` | Timeout in seconds for catalog calls. |
| `CART_TTL_SECONDS` | `604800` | Cart expiry in seconds (default 7 days). |
| `CART_MAX_ITEMS` | `50` | Maximum unique items per cart. |
| `CART_MAX_QUANTITY_PER_ITEM` | `99` | Maximum quantity for a single line item. |
| `PORT` | `8002` | Gunicorn bind port. |
| `LOG_LEVEL` | `INFO` | Logging level. |

### Orders Service

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | — | Required. |
| `DATABASE_URL` | — | PostgreSQL connection string. |
| `CART_SERVICE_URL` | `http://cart-service:8002` | Internal URL of the Cart Service. |
| `CART_SERVICE_TIMEOUT` | `5` | Timeout in seconds for cart calls. |
| `CANCELLABLE_STATUSES` | `PENDING,CONFIRMED` | Order statuses that allow cancellation. |
| `PORT` | `8003` | Gunicorn bind port. |
| `LOG_LEVEL` | `INFO` | Logging level. |

### UI Service

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | — | Required. |
| `DJANGO_DEBUG` | `False` | Enable debug mode. |
| `CATALOG_SERVICE_URL` | `http://catalog-service:8001` | Internal URL of the Catalog Service. |
| `CART_SERVICE_URL` | `http://cart-service:8002` | Internal URL of the Cart Service. |
| `ORDERS_SERVICE_URL` | `http://orders-service:8003` | Internal URL of the Orders Service. |
| `SERVICE_TIMEOUT` | `8` | Timeout in seconds for all backend calls. |
| `PRODUCTS_PER_PAGE` | `12` | Number of products shown per listing page. |
| `GUNICORN_PORT` | `8080` | Internal Gunicorn bind port (Nginx proxies to this). |
| `LOG_LEVEL` | `INFO` | Logging level. |

---

## API Reference

Each backend service generates an OpenAPI 3 schema via drf-spectacular.

| Service | Schema URL | Swagger UI |
|---|---|---|
| Catalog | `http://localhost:8001/api/schema/` | `http://localhost:8001/api/docs/` |
| Cart | `http://localhost:8002/api/schema/` | `http://localhost:8002/api/docs/` |
| Orders | `http://localhost:8003/api/schema/` | `http://localhost:8003/api/docs/` |

### Catalog Service endpoints

```
GET  /api/v1/catalog/products/               List products (paginated, filterable)
GET  /api/v1/catalog/products/<id>/          Retrieve a single product
GET  /api/v1/catalog/products/featured/      List featured products
GET  /api/v1/catalog/products/search/?q=     Full-text search
GET  /api/v1/catalog/categories/             List categories
GET  /api/v1/catalog/categories/<id>/        Retrieve a single category
GET  /health/                                Health check
```

### Cart Service endpoints

All cart endpoints require the `X-Session-Key: <key>` header.

```
GET    /api/v1/cart/         Retrieve the cart for the session
POST   /api/v1/cart/add/     Add a product to the cart
PUT    /api/v1/cart/update/  Update the quantity of a cart item
DELETE /api/v1/cart/remove/  Remove a single item from the cart
DELETE /api/v1/cart/clear/   Clear the entire cart
GET    /health/              Health check
```

### Orders Service endpoints

Order endpoints require the `X-User-Id: <id>` header.

```
GET  /api/v1/orders/                  List orders for the user (paginated)
POST /api/v1/orders/place/            Place a new order from the current cart
GET  /api/v1/orders/<id>/             Retrieve a single order
PUT  /api/v1/orders/<id>/cancel/      Cancel an order
GET  /health/                         Health check
```

---

## Data Models

### Catalog Service

**Product**

| Field | Type | Notes |
|---|---|---|
| `sku` | string | Unique stock keeping unit |
| `name` | string | |
| `slug` | string | Auto-generated from name |
| `description` | text | |
| `category` | FK Category | |
| `brand` | string | |
| `tags` | string | Comma-separated |
| `price` | decimal | Base / MRP price |
| `discount_percent` | decimal | 0–100 |
| `selling_price` | computed | `price * (1 - discount_percent / 100)` |
| `stock_quantity` | integer | |
| `status` | enum | `draft`, `active`, `archived`, `out_of_stock` |
| `is_featured` | boolean | |
| `rating_avg` | decimal | 0–5, denormalised |
| `rating_count` | integer | |

**ProductImage** — one-to-many images per product with `is_primary` flag.

**ProductAttribute** — flexible key-value pairs per product (e.g. `colour=Red`, `weight=250g`).

### Cart Service

Cart data is stored entirely in Redis. No relational database is used.

**CartItem** — `product_id`, `quantity`, `price` (string, frozen at add time), `name`, `sku`, `currency`.

**Cart** — aggregated view: `items[]`, `total_items`, `subtotal`, `session_key`.

Redis key layout: `data:<session_key>` maps to a JSON object of line items keyed by `product_id`.

### Orders Service

**Order**

| Field | Type | Notes |
|---|---|---|
| `user_id` | string | Anonymous guest ID or future auth user UUID |
| `session_key` | string | Cart session used when placing the order |
| `total_price` | decimal | Frozen at placement time |
| `status` | enum | `PENDING`, `CONFIRMED`, `SHIPPED`, `DELIVERED`, `CANCELLED` |
| `shipping_name` | string | |
| `shipping_address_line1` | string | |
| `shipping_city` | string | |
| `shipping_pincode` | string | |
| `shipping_country` | string | Default `India` |
| `notes` | text | |
| `cancellation_reason` | text | |

**OrderItem** — immutable snapshot: `product_id`, `product_name`, `product_sku`, `quantity`, `unit_price`. Prices are frozen so that future catalogue changes do not alter historical orders.

**Order status transitions**

```
PENDING --> CONFIRMED --> SHIPPED --> DELIVERED
   |              |
   v              v
CANCELLED     CANCELLED
```

---

## Running Tests

Each service has its own test suite using pytest and pytest-django.

```bash
cd retail-store/services/catalog
pip install -r requirements.txt
pytest

cd ../cart
pip install -r requirements.txt
pytest

cd ../orders
pip install -r requirements.txt
pytest
```

Test configuration is defined in each service's `pytest.ini`. Factory-boy and Faker are used for test data generation. The Cart Service tests use `fakeredis` so no real Redis instance is required.

---

## Docker

Each service has a multi-stage Dockerfile:

- **Stage 1 (builder)** — installs Python dependencies and collects Django static files.
- **Stage 2 (runtime)** — copies the virtual environment and app from the builder. The UI Service additionally installs Nginx and Supervisord to serve static files and manage both processes in a single container.

### UI Service container layout

```
Port 80   <-- Nginx (static files + proxy)
              |
Port 8080 <-- Gunicorn (Django)
              (managed together by Supervisord)
```

### Build a single service image

```bash
cd retail-store/services/ui
docker build -t retail-ui:latest .
```

### Run a single service image

```bash
docker run -p 80:80 \
  -e DJANGO_SECRET_KEY="your-secret-key" \
  -e CATALOG_SERVICE_URL="http://host.docker.internal:8001" \
  -e CART_SERVICE_URL="http://host.docker.internal:8002" \
  -e ORDERS_SERVICE_URL="http://host.docker.internal:8003" \
  retail-ui:latest
```

---

## Service Communication

```
UI Service
  --> GET  /api/v1/catalog/products/featured/   (Catalog)
  --> GET  /api/v1/catalog/products/            (Catalog)
  --> GET  /api/v1/catalog/products/<id>/       (Catalog)
  --> GET  /api/v1/catalog/categories/          (Catalog)
  --> GET  /api/v1/cart/          X-Session-Key (Cart)
  --> POST /api/v1/cart/add/      X-Session-Key (Cart)
  --> PUT  /api/v1/cart/update/   X-Session-Key (Cart)
  --> DELETE /api/v1/cart/remove/ X-Session-Key (Cart)
  --> DELETE /api/v1/cart/clear/  X-Session-Key (Cart)
  --> POST /api/v1/orders/place/                (Orders)
  --> GET  /api/v1/orders/        X-User-Id     (Orders)
  --> GET  /api/v1/orders/<id>/   X-User-Id     (Orders)
  --> PUT  /api/v1/orders/<id>/cancel/ X-User-Id (Orders)

Orders Service
  --> GET /api/v1/cart/  X-Session-Key          (Cart — reads cart at placement time)
  --> DELETE /api/v1/cart/clear/ X-Session-Key  (Cart — clears cart after placing order)

Cart Service
  --> GET /api/v1/catalog/products/<id>/        (Catalog — validates product before adding)
```

---

## Contributing

1. Create a feature branch from `main`.
2. Make changes inside the relevant service directory. Avoid cross-service changes in a single commit.
3. Write or update tests for any logic changes.
4. Ensure all tests pass before opening a pull request.
5. Keep each service self-contained — do not add imports or dependencies that cross service boundaries.

---

## Troubleshooting

### CSRF 403 Errors
If you encounter CSRF verification errors when submitting forms:
- The UI service includes `CSRF_TRUSTED_ORIGINS` configuration for localhost
- Ensure cookies are enabled in your browser
- Clear browser cookies and reload the page

### Products Not Adding to Cart
- Verify all services are healthy: `docker compose ps`
- Check cart service logs: `docker compose logs cart-service --tail 50`
- Ensure catalog service is responding: `curl http://localhost/api/v1/catalog/products/`

### Database Migration Issues
- Migrations are included in the repository
- If needed, regenerate with: `docker compose exec catalog-service python manage.py makemigrations`
- Apply migrations: `docker compose exec catalog-service python manage.py migrate`

### Service Health Checks
```bash
# Check all container status
docker compose ps

# View specific service logs
docker compose logs <service-name> -f

# Restart a single service
docker compose restart <service-name>

# Rebuild and restart a service
docker compose up --build -d --no-deps <service-name>
```
