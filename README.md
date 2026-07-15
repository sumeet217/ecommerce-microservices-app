# RetailStore — Django Microservices E-Commerce

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.0-092E20?logo=django&logoColor=white)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.15-red)](https://www.django-rest-framework.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-24%2B-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![GitLab CI/CD](https://img.shields.io/badge/CI%2FCD-GitLab-orange?logo=gitlab)](https://gitlab.com)
[![DevSecOps](https://img.shields.io/badge/DevSecOps-Enabled-success)](https://devsecops.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A production-ready e-commerce platform built with microservices architecture using Django and Django REST Framework. Each service is independently deployable, scalable, and owns its data store, following best practices for distributed systems.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Services](#services)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [CI/CD Pipeline](#cicd-pipeline)
- [API Documentation](#api-documentation)
- [Security](#security)
- [Testing](#testing)
- [Docker Images](#docker-images)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Microservices Architecture**: Independent services with dedicated databases
- **RESTful APIs**: Complete OpenAPI/Swagger documentation for all endpoints
- **JWT Authentication**: Secure token-based authentication with refresh and blacklisting
- **Session-based Cart**: Redis-backed shopping cart with automatic expiration
- **Order Management**: Complete order lifecycle with status tracking
- **Product Catalog**: Full-text search, categories, and inventory management
- **Responsive UI**: Server-side rendered storefront using Django templates and Bootstrap 5
- **Docker Ready**: Full containerization with Docker Compose orchestration
- **Production Grade**: Rate limiting, health checks, and proper error handling
- **Comprehensive Tests**: pytest-based test suite with factory patterns
- **DevSecOps Pipeline**: GitLab CI/CD with security scanning and quality gates
- **AWS Deployment**: Automated EC2 deployment with rollback capability

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     🌐  Internet / Browser                       │
└────────────────────────────────┬────────────────────────────────┘
                                 │  Port 80
                    ┌────────────▼────────────┐
                    │       Nginx Proxy        │
                    │  routing + static files  │
                    └──┬────┬─────┬──────┬────┘
                       │    │     │      │
         /api/v1/auth/ │    │     │      │ /api/v1/orders/
      /api/v1/catalog/ │    │     │      │
          /api/v1/cart/│    │     │      │
                       │    │  /  │      │
          ┌────────────▼┐   │  ┌──▼──────▼────┐   ┌────────────────┐
          │Auth Service │   │  │  UI Service  │   │Orders Service  │
          │  Port 8000  │   │  │  Nginx :80   │   │  Port 8003     │
          │ Django+JWT  │   │  │  Gunicorn    │   │  Django REST   │
          └──────┬──────┘   │  │  Port 8000   │   └───────┬────────┘
                 │           │  └──────────────┘           │
          ┌──────▼──────┐   │                         ┌────▼──────┐
          │   auth-db   │   │  ┌────────────────┐     │ orders-db │
          │  Postgres   │   │  │Catalog Service │     │ Postgres  │
          └─────────────┘   │  │  Port 8001     │     └───────────┘
                            │  │  DRF + PG      │
                            │  └───────┬────────┘
                            │      ┌───▼──────┐    ┌────────────────┐
                            │      │catalog-db│    │  Cart Service  │
                            │      │ Postgres │    │   Port 8002    │
                            │      └──────────┘    │   DRF+Redis   │
                            │                      └───────┬────────┘
                            │                          ┌───▼───┐
                            └──────────────────────────│ Redis │
                                                       │ :6379 │
                                                       └───────┘
```

> The UI Service is the only service exposed to the browser. It acts as a BFF, calling backend APIs over the internal Docker network.

## 📸 Screenshots

> **To add screenshots:** Take the images below and save them to the `images/` folder, then the README will display them automatically.

### Storefront

| Home Page | Product Listing | Product Detail |
|-----------|----------------|----------------|
| ![Home](images/screenshot-home.png) | ![Products](images/screenshot-products.png) | ![Detail](images/screenshot-product-detail.png) |

| Cart | Checkout | Orders |
|------|----------|--------|
| ![Cart](images/screenshot-cart.png) | ![Checkout](images/screenshot-checkout.png) | ![Orders](images/screenshot-orders.png) |

> 📷 **Screenshots to take:** Open `http://52.23.154.161` and capture each page above. Save as `images/screenshot-<name>.png`

---

---

## Services Overview

| Service | Port | Database | Responsibility |
|---|---|---|---|
| **Auth Service** | 8004 | PostgreSQL | User registration, JWT authentication, token management |
| **Catalog Service** | 8001 | PostgreSQL | Products, categories, search, inventory |
| **Cart Service** | 8002 | Redis | Session-based shopping cart |
| **Orders Service** | 8003 | PostgreSQL | Order placement, status lifecycle |
| **UI Service** | 80 (nginx) / 8000 (gunicorn) | — | Server-rendered storefront (Django Templates + Bootstrap 5) |

### Auth Service
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

## Tech Stack

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

## Local Setup (Docker Compose)

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
| http://localhost:3000 | Direct UI (bypasses Nginx, mapped in docker-compose) |
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

## Production Deployment (AWS EC2)

### EC2 Security Group — Required Inbound Rules

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Your IP only | SSH access |
| 80 | TCP | 0.0.0.0/0 | Nginx (main entry point for all traffic) |

> ⚠️ Port 3000 (direct UI) and 8004 (auth) are only needed for debugging — keep them closed in production.

### First-time EC2 Setup

```bash
# 1. SSH into your EC2 instance
ssh -i your-key.pem ubuntu@<EC2_IP>

# 2. Clone the repository
git clone https://github.com/sumeet217/ecommerce-microservices-app.git
cd ecommerce-microservices-app

# 3. Create and configure .env (NEVER commit this file)
cp .env.example .env
nano .env
```

### ⚠️ Critical: .env changes required for production

The `.env` file is gitignored and must be manually edited on the server.
Add your EC2 public IP to **all five** `ALLOWED_HOSTS` entries:

```bash
# Replace <EC2_IP> with your actual public IP (e.g. 52.23.154.161)
UI_DJANGO_ALLOWED_HOSTS=ui-service,localhost,127.0.0.1,nginx,<EC2_IP>
AUTH_DJANGO_ALLOWED_HOSTS=auth-service,localhost,127.0.0.1,<EC2_IP>
CATALOG_DJANGO_ALLOWED_HOSTS=catalog-service,localhost,127.0.0.1,<EC2_IP>
CART_DJANGO_ALLOWED_HOSTS=cart-service,localhost,127.0.0.1,<EC2_IP>
ORDERS_DJANGO_ALLOWED_HOSTS=orders-service,localhost,127.0.0.1,<EC2_IP>
```

### Deploy

```bash
# Start all services
docker compose -f docker-compose.prod.yml up -d

# Rebuild a single service after code changes (e.g. ui-service)
docker compose -f docker-compose.prod.yml up -d --build ui-service

# Watch logs
docker compose -f docker-compose.prod.yml logs -f nginx ui-service

# Health check
curl -I http://<EC2_IP>
```

### Production Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `404` from nginx | Port mismatch between Gunicorn and ui-service internal nginx | Verify `UI_GUNICORN_PORT=8000` in `.env` and `upstream django_ui { server 127.0.0.1:8000; }` in `nginx/nginx.conf` |
| `400 Bad Request` | EC2 IP missing from `DJANGO_ALLOWED_HOSTS` | Add public IP to all `*_DJANGO_ALLOWED_HOSTS` in `.env` on the server |
| `403 CSRF` on POST | EC2 URL missing from `CSRF_TRUSTED_ORIGINS` | Add `http://<EC2_IP>` to `CSRF_TRUSTED_ORIGINS` in `docker-compose.prod.yml` |
| `502 Bad Gateway` | Upstream service not running or not healthy | Run `docker ps` to check container health |

---

## DockerHub Images

Pre-built images are available on Docker Hub:

| Service | Image |
|---|---|
| Catalog Service | [`sumeet217/retailstore-catalog`](https://hub.docker.com/r/sumeet217/retailstore-catalog) |
| Cart Service | [`sumeet217/retailstore-cart`](https://hub.docker.com/r/sumeet217/retailstore-cart) |
| Orders Service | [`sumeet217/retailstore-orders`](https://hub.docker.com/r/sumeet217/retailstore-orders) |
| UI Service | [`sumeet217/retailstore-ui`](https://hub.docker.com/r/sumeet217/retailstore-ui) |

> **Auth Service** is built locally from `./retail-store/services/auth` via `docker compose up --build`.

---

## CI/CD Pipeline

This project includes a **production-ready DevSecOps CI/CD pipeline** for GitLab, featuring automated testing, security scanning, quality gates, and AWS EC2 deployment.

### 🎯 Pipeline Stages

```
CLONE → TEST → SECURITY SCAN → QUALITY GATE → BUILD → DEPLOY
 ~10s    ~4m       ~7m             ~30s         ~3m     ~4m
```

### 📸 Pipeline Screenshots

**Jenkins Pipeline Overview**
![Jenkins Pipeline](images/jenkins-pipeline-overview.png)
> 📷 Go to `http://<EC2_IP>:8080` → your pipeline job → take a screenshot of the stage view

**Jenkins Pipeline Success**
![Jenkins Success](images/jenkins-pipeline-success.png)
> 📷 Screenshot of a successful pipeline run showing all green stages

**SonarQube Quality Gate**
![SonarQube Dashboard](images/sonarqube-dashboard.png)
> 📷 Go to `http://<EC2_IP>:9000` → your project → screenshot the main dashboard

**SonarQube Issues & Coverage**
![SonarQube Issues](images/sonarqube-issues.png)
> 📷 Screenshot the Issues or Measures tab in SonarQube

### 🛡️ Security & Quality Features

| Category | Tools |
|----------|-------|
| **Code Quality** | pytest, coverage, flake8, black, isort |
| **Security Scanning** | SonarQube, OWASP Dependency Check, Bandit, Trivy |
| **Quality Gates** | Automated enforcement, pipeline fails on critical issues |
| **Deployment** | Automated EC2 deployment, health checks, rollback |

### 📦 CI/CD Files Location

All CI/CD configuration is in the `retail-store/` directory:

```
retail-store/
├── .gitlab-ci.yml              # Main CI/CD pipeline (6 stages)
├── sonar-project.properties    # SonarQube configuration
├── suppression.xml             # OWASP suppression rules
├── setup-ec2.sh                # EC2 instance setup script
├── README_CI_CD.md             # CI/CD overview
├── CI_CD_SETUP.md              # Detailed setup guide
├── QUICK_REFERENCE.md          # Quick operations reference
├── PIPELINE_ARCHITECTURE.md    # Visual architecture docs
└── IMPLEMENTATION_SUMMARY.md   # Implementation summary
```

### 🚀 Quick Setup

1. **Configure GitLab Variables** (Settings → CI/CD → Variables):
   ```
   SONAR_HOST_URL      # SonarQube server URL
   SONAR_TOKEN         # SonarQube auth token (Masked)
   AWS_DEFAULT_REGION  # AWS region (e.g., us-east-1)
   EC2_HOST            # EC2 instance IP or hostname
   EC2_USER            # SSH user (e.g., ubuntu)
   SSH_PRIVATE_KEY     # SSH private key content (File, Masked)
   ```

2. **Setup EC2 Instance**:
   ```bash
   # Copy and run setup script on EC2
   scp retail-store/setup-ec2.sh ubuntu@<EC2_HOST>:~/
   ssh ubuntu@<EC2_HOST>
   sudo ./setup-ec2.sh
   ```

3. **Push Code to Trigger Pipeline**:
   ```bash
   git add .
   git commit -m "feat: add CI/CD pipeline"
   git push
   ```

### 📊 Service Architecture on EC2

```
Internet → Nginx (Port 80) → Django Services
                               ├── Auth (8001)
                               ├── Catalog (8002)
                               ├── Cart (8003)
                               ├── Orders (8004)
                               └── UI (8000)
```

All services run as systemd services with automatic restarts and health monitoring.

### 📚 Detailed Documentation

- **[README_CI_CD.md](retail-store/README_CI_CD.md)** - Complete CI/CD overview
- **[CI_CD_SETUP.md](retail-store/CI_CD_SETUP.md)** - Step-by-step setup instructions
- **[QUICK_REFERENCE.md](retail-store/QUICK_REFERENCE.md)** - Common commands and operations
- **[PIPELINE_ARCHITECTURE.md](retail-store/PIPELINE_ARCHITECTURE.md)** - Visual pipeline diagrams

### 🔍 Security Scanning

The pipeline performs comprehensive security scanning:

1. **SonarQube**: Code quality, security hotspots, code smells
2. **OWASP Dependency Check**: Known CVEs in Python dependencies
3. **Bandit**: Python-specific security linting
4. **Trivy**: Filesystem vulnerability scanning

Quality gates enforce standards - **critical issues block deployment**.

**OWASP Dependency Check Report**
![OWASP Report](images/owasp-dependency-report.png)
> 📷 Screenshot the HTML report generated in the pipeline artifacts

**Trivy Scan Results**
![Trivy Scan](images/trivy-scan-results.png)
> 📷 Screenshot from the Jenkins console output of the Trivy stage

### 🎯 Deployment Process

1. **Automated Testing**: All tests must pass
2. **Security Scanning**: No critical vulnerabilities
3. **Quality Gate**: SonarQube standards enforced
4. **Build Artifacts**: Deployment package created
5. **Manual Approval**: Deploy to production (main branch only)
6. **Health Checks**: Automatic verification post-deployment
7. **Rollback**: One-click rollback to previous version

---

## API Endpoints

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

### 📸 API Documentation Screenshots

**Auth API — Swagger UI**
![Auth API Docs](images/api-docs-auth.png)
> 📷 Open `http://52.23.154.161/api/docs/auth/` and screenshot the Swagger UI

**Catalog API — Swagger UI**
![Catalog API Docs](images/api-docs-catalog.png)
> 📷 Open `http://52.23.154.161/api/docs/catalog/` and screenshot the Swagger UI

---

## Security

### Application Security

| Feature | Implementation |
|---|---|
| Password hashing | PBKDF2 (Django default) |
| JWT algorithm | HS256 |
| Token blacklisting | `rest_framework_simplejwt.token_blacklist` |
| Login rate limiting | 10 requests/minute (ScopedRateThrottle) |
| UUID user IDs | Prevents sequential enumeration |
| Email normalisation | Case-insensitive, lowercased on register & login |
| CORS | Configurable per-service via `CORS_ALLOWED_ORIGINS` |

### CI/CD Security

The GitLab pipeline includes **4 layers of security scanning**:

| Tool | Purpose | Blocks Pipeline |
|------|---------|-----------------|
| **SonarQube** | Code quality & security hotspots | ✅ Quality gate |
| **OWASP Dependency Check** | Known CVEs in dependencies | ✅ Critical vulns |
| **Bandit** | Python security linting | ⚠️ Warning only |
| **Trivy** | Filesystem vulnerabilities | ✅ Critical vulns |

**Security Best Practices Enforced:**
- ✅ No hardcoded secrets (GitLab masked variables)
- ✅ SSH key-based authentication only
- ✅ Automated backup before deployment
- ✅ Quality gates block vulnerable code
- ✅ Security scan reports in every pipeline run

---

## Running Tests

Each service has an independent test suite using pytest, factory-boy, and Faker. Tests run against SQLite in-memory — no real database required.

### Local Testing

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

### CI/CD Testing

The GitLab pipeline automatically runs:

- ✅ **Unit Tests**: All services tested in parallel
- ✅ **Code Coverage**: Cobertura reports generated
- ✅ **Linting**: flake8, black, isort checks
- ✅ **Security Linting**: Bandit for Python security issues

**Test Reports Available:**
- JUnit XML (test results)
- Cobertura XML (coverage reports)
- HTML reports (downloadable artifacts)

Pipeline **fails automatically** if tests don't pass.

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please ensure your code follows the existing style and includes appropriate tests.

---

## Author

**Sumeet Mankari**
- GitHub: [@sumeet217](https://github.com/sumeet217)
- Project: [ecommerce-microservices-app](https://github.com/sumeet217/ecommerce-microservices-app)

---

## License

This project is licensed under the MIT License.
