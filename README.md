# ClinicFlow - Medical Prescription & Payment System

A microservices-based backend system for managing clinical prescriptions, drug inventory, invoicing, and payment processing. Built with an event-driven architecture using composite orchestration, API gateway routing, and asynchronous notifications.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Service Endpoints](#service-endpoints)
- [Request Flows](#request-flows)
- [Prerequisites](#prerequisites)
- [Setup & Running](#setup--running)
- [Frontend](#frontend)
- [Kong API Gateway](#kong-api-gateway)
- [Scaling Services](#scaling-services)
- [Monitoring (Prometheus & Grafana)](#monitoring-prometheus--grafana)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Database Reference](#database-reference)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Overview

ClinicFlow automates two core clinical workflows:

1. **Prescribe Medicine** — A doctor selects drugs for a patient record. The system deducts inventory, creates prescription records, calculates totals, and generates an invoice.
2. **Make Payment** — A patient pays an invoice via Stripe. The system processes the payment, updates statuses, and sends an SMS confirmation via Twilio.

The backend is composed of **atomic services** (single-responsibility CRUD) orchestrated by **composite services** that coordinate multi-step business flows with rollback support.

---

## Architecture

```
                         ┌──────────────┐
                         │   Frontend   │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │  Kong (8000) │  API Gateway
                         └──────┬───────┘
                    ┌───────────┼───────────┐
                    │                       │
          ┌─────────▼──────────┐  ┌─────────▼──────────┐
          │ Prescribe Medicine │  │   Make Payment     │  Composites
          │     (5007)         │  │     (5008)         │
          └──┬─────┬────┬──────┘  └──┬──────┬────┬─────┘
             │     │    │            │      │    │
    ┌────────▼┐ ┌──▼───┐ ┌──▼────┐ ┌─▼──────┐ ┌─▼──────┐ ┌──▼──────────┐
    │  Drug   │ │Presc.│ │Invoice│ │Invoice │ │Payment │ │ RabbitMQ    │
    │Catalogue│ │Svc   │ │ Svc   │ │ Svc    │ │ Svc    │ │  (5672)     │
    │ (5001)  │ │(5005)│ │(5003) │ │(5003)  │ │(5004)  │ └──┬──────────┘
    └────┬────┘ └──┬───┘ └──┬────┘ └────────┘ └──┬─────┘    │
         │         │        │                     │      ┌───▼───────────┐
         └─────────┴────┬───┘                     │      │ Notification  │
                        │                         │      │   Service     │
                   ┌────▼────┐              ┌─────▼──┐   └───┬───────────┘
                   │Postgres │              │ Stripe │       │
                   │ (5432)  │              │  API   │   ┌───▼───┐
                   └─────────┘              └────────┘   │Twilio │
                                                         │  API  │
                                                         └───────┘
```

### Service Types

| Type | Description | Services |
|------|-------------|----------|
| **Atomic** | Single-responsibility CRUD microservices | Drug Catalogue, Prescription, Invoice, Payment |
| **Composite** | Multi-step orchestrators with rollback | Prescribe Medicine, Make Payment |
| **Async** | Event-driven consumer | Notification Service |
| **External** | OutSystems REST APIs | Clinical Records, Patient, Consultation |
| **Infrastructure** | Platform services | PostgreSQL, RabbitMQ, Kong |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Atomic Services** | Python, FastAPI, SQLAlchemy, Pydantic |
| **Composite Services** | Python, Flask, Requests |
| **Database** | PostgreSQL 16 (shared DB, isolated schemas) |
| **Message Broker** | RabbitMQ 4 (pika client) |
| **API Gateway** | Kong 3.9 (Postgres-backed with Admin API) |
| **Payments** | Stripe API |
| **Notifications** | Twilio SMS |
| **Frontend** | Vue 3, Vite, Vue Router, Tailwind CSS, Axios |
| **UI Components** | Lucide Vue Next (icons), Stripe.js (card element) |
| **Containerization** | Docker, Docker Compose |

---

## Service Endpoints

All external traffic routes through **Kong at `http://localhost:8000`**.

### Drug Catalogue Service — `/drug`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/drug` | Create a new drug |
| `GET` | `/drug` | List all drugs |
| `GET` | `/drug/{drug_id}` | Get drug by ID |
| `GET` | `/drug/name/{drug_name}` | Get drug by name (case-insensitive) |
| `PUT` | `/drug/{drug_id}` | Full update (name, quantity, price) |
| `PATCH` | `/drug/{drug_id}/quantity` | Set quantity to exact value |
| `PATCH` | `/drug/{drug_id}/deduct` | Atomically deduct stock (409 if insufficient) |
| `PATCH` | `/drug/{drug_id}/restore` | Atomically restore stock (rollback) |
| `DELETE` | `/drug/{drug_id}` | Delete a drug |

### Payment Service — `/payments`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/payments/intents` | Create Stripe payment intent |
| `GET` | `/payments/{payment_id}` | Get payment by ID |
| `GET` | `/payments/invoice/{invoice_id}` | List payments for invoice |
| `GET` | `/payments/invoice/{invoice_id}/latest` | Get latest payment for invoice |
| `POST` | `/payments/{payment_id}/cancel` | Cancel a payment |
| `POST` | `/payments/webhook` | Stripe webhook receiver |

### Prescribe Medicine (Composite) — `/prescribe`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/prescribe/{record_id}` | Orchestrate full prescription workflow |

**Request:**
```json
{
  "drugs": [
    { "drugId": 1, "quantity": 2 },
    { "drugId": 3, "quantity": 1 }
  ]
}
```

**Response (201):**
```json
{
  "recordId": 1,
  "drugs": [
    {
      "drugId": 1,
      "drugName": "Aspirin",
      "quantity": 2,
      "unitPrice": "5.00",
      "lineTotal": "10.00",
      "prescriptionId": 1
    }
  ],
  "totalPrice": "10.00",
  "status": "success"
}
```

### Make Payment (Composite) — `/make_payment`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/make_payment/initiate-payment` | Initiate payment for an invoice |
| `POST` | `/make_payment/retry-payment` | Retry a failed payment |
| `POST` | `/make_payment/payment-events` | Internal webhook for payment events |
| `GET` | `/make_payment/health` | Health check |

### Internal Services (not exposed through Kong)

These services are called internally by composites and are not directly accessible from outside Docker.

**Invoice Service (5003):**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/invoice` | Create invoice |
| `GET` | `/invoice` | List all invoices |
| `GET` | `/invoice/{invoice_id}` | Get invoice by ID |
| `GET` | `/invoice/record/{record_id}` | Get invoice by record ID |
| `PUT` | `/invoice/{invoice_id}/total` | Update total |
| `PUT` | `/invoice/{invoice_id}/payment-pending` | Mark payment pending |
| `PUT` | `/invoice/{invoice_id}/paid` | Mark as paid |
| `PUT` | `/invoice/{invoice_id}/failed` | Mark as failed |
| `PUT` | `/invoice/{invoice_id}/cancelled` | Mark as cancelled |
| `DELETE` | `/invoice/{invoice_id}` | Delete invoice |

**Prescription Service (5005):**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/prescription` | Create prescription |
| `GET` | `/prescription` | List all prescriptions |
| `GET` | `/prescription/{id}` | Get by ID |
| `GET` | `/prescription/record/{record_id}` | Get by record |
| `PUT` | `/prescription/{id}` | Update prescription |
| `DELETE` | `/prescription/{id}` | Delete prescription |
| `DELETE` | `/prescription/record/{record_id}` | Delete all for record |

---

## Request Flows

### Scenario 1: Prescribe Medicine

```
Client                   Kong            Prescribe Medicine     Drug Catalogue    Prescription Svc    Invoice Svc
  │                        │                    │                     │                  │                │
  │ POST /prescribe/1      │                    │                     │                  │                │
  │───────────────────────>│                    │                     │                  │                │
  │                        │───────────────────>│                     │                  │                │
  │                        │                    │  GET /drug/{id}     │                  │                │
  │                        │                    │────────────────────>│                  │                │
  │                        │                    │<────────────────────│                  │                │
  │                        │                    │  PATCH /drug/deduct │                  │                │
  │                        │                    │────────────────────>│                  │                │
  │                        │                    │<────────────────────│                  │                │
  │                        │                    │                     │                  │                │
  │                        │                    │  POST /prescription │                  │                │
  │                        │                    │────────────────────────────────────── >│                │
  │                        │                    │<───────────────────────────────────────│                │
  │                        │                    │                     │                  │                │
  │                        │                    │  POST /invoice      │                  │                │
  │                        │                    │───────────────────────────────────────────────────────> │
  │                        │                    │<────────────────────────────────────────────────────────│
  │                        │                    │                     │                  │                │
  │                        │<───────────────────│                     │                  │                │
  │<───────────────────────│  201 Created       │                     │                  │                │
```

**Rollback:** If any step fails, the orchestrator restores deducted drug stock and deletes created prescriptions.

### Scenario 2: Make Payment

```
Client              Kong           Make Payment       Invoice Svc     Payment Svc      RabbitMQ      Notification
  │                   │                 │                  │               │               │               │
  │ POST /make_payment│                 │                  │               │               │               │
  │  /initiate-payment│                 │                  │               │               │               │
  │──────────────────>│                 │                  │               │               │               │
  │                   │────────────────>│                  │               │               │               │
  │                   │                 │ GET /invoice/{id}│               │               │               │
  │                   │                 │─────────────────>│               │               │               │
  │                   │                 │<─────────────────│               │               │               │
  │                   │                 │                  │               │               │               │
  │                   │                 │ POST /payments/intents           │               │               │
  │                   │                 │─────────────────────────────────>│               │               │
  │                   │                 │<─────────────────────────────────│               │               │
  │                   │                 │                  │               │               │               │
  │                   │                 │ PUT /invoice/payment-pending     │               │               │
  │                   │                 │─────────────────>│               │               │               │
  │                   │                 │                  │               │               │               │
  │                   │                 │ publish notification             │               │               │
  │                   │                 │──────────────────────────────────────────────── >│               │
  │                   │                 │                  │               │               │  consume      │
  │                   │                 │                  │               │               │──────────────>│
  │                   │                 │                  │               │               │               │── SMS via Twilio
  │                   │<────────────────│                  │               │               │               │
  │<──────────────────│  200 OK         │                  │               │               │               │
```

---

## Prerequisites

| Tool | Purpose |
|------|---------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Container runtime |
| [Git](https://git-scm.com/) | Clone the repository |
| [Stripe Account](https://dashboard.stripe.com/test/apikeys) | Payment processing (test keys) |
| [Twilio Account](https://www.twilio.com/) | SMS notifications (optional) |

Ensure **Docker Desktop is running** before proceeding.

---

## Setup & Running

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ESD_G4T2
```

### 2. Configure Environment Variables

All `.env` files are gitignored. Create them from the provided `.example` templates.

#### 2a. PostgreSQL Credentials

```bash
cp backend/.env.postgres.example backend/.env.postgres
```

```env
POSTGRES_USER=USER
POSTGRES_PASSWORD=PASSWORD
```

#### 2b. Docker Environment (Recommended)

All services share a single `.env.docker` file loaded by Docker Compose:

```bash
cp backend/.env.docker.example backend/.env.docker
```

Edit `backend/.env.docker` and fill in your Stripe and Twilio credentials. This file configures database, RabbitMQ, internal service URLs, external OutSystems URLs, and all secrets in one place.

#### 2c. Per-Service Environment Files (Local Development)

For running services locally outside Docker, each service needs its own `.env`:

```bash
# Atomic services
cp backend/services/invoice_service/.env.example    backend/services/invoice_service/.env
cp backend/services/drug_catalogue_service/.env.example backend/services/drug_catalogue_service/.env
cp backend/services/prescription_service/.env.example backend/services/prescription_service/.env
cp backend/services/payment_service/.env.example    backend/services/payment_service/.env

# Composite services
cp backend/composites/prescribe_medicine/.env.example backend/composites/prescribe_medicine/.env
cp backend/composites/make_payment/.env.example     backend/composites/make_payment/.env
```

**Key configuration per service:**

| Service | Critical Variables |
|---------|-------------------|
| All DB services | `DB_HOST=postgres`, `DB_USER=clinic`, `DB_PASSWORD=clinic`, `DB_NAME=esd_db` |
| Payment Service | `STRIPE_SECRET_KEY=sk_test_...`, `STRIPE_WEBHOOK_SECRET=whsec_...` |
| Prescribe Medicine | `DRUG_CATALOGUE_URL=http://drug_service:5001`, `INVOICE_SERVICE_URL=http://invoice_service:5003`, `PRESCRIPTION_SERVICE_URL=http://prescription_service:5005` |
| Make Payment | `INVOICE_SERVICE_URL=http://invoice_service:5003`, `PAYMENT_SERVICE_URL=http://payment_service:5004`, `RABBITMQ_HOST=rabbitmq` |

> **Important:** When running via Docker Compose, use Docker service names as hostnames (e.g., `postgres`, `drug_service`). When running locally, use `localhost`.

#### 2d. Stripe Keys

1. Go to [Stripe Dashboard > Test API Keys](https://dashboard.stripe.com/test/apikeys)
2. Copy the **Secret key** (`sk_test_...`) into `payment_service/.env`
3. For webhooks: **Developers > Webhooks** > copy the signing secret (`whsec_...`)

### 3. Build and Start All Services

```bash
cd backend
docker compose up -d --build
```

This starts:
- **PostgreSQL** — app database (runs `db/init.sql` on first boot)
- **Kong database** — separate Postgres for Kong
- **Kong migration** — bootstraps Kong schema (runs once)
- **Kong** — API gateway
- **RabbitMQ** — message broker
- **4 atomic services** — Drug Catalogue, Prescription, Invoice, Payment
- **2 composite services** — Prescribe Medicine, Make Payment
- **Prometheus** — metrics collection and alerting
- **Grafana** — monitoring dashboards (auto-provisioned)

### 4. Configure Kong Routes

After all containers are healthy, run the setup script:

```bash
./kong-setup.sh
```

This registers upstreams, services, routes, and enables the Prometheus monitoring plugin.

### 5. Verify

```bash
# Check all containers are running
docker compose ps

# Test through Kong
curl http://localhost:8000/drug

# Access Kong Manager GUI
open http://localhost:8002

# Access Grafana dashboard
open http://localhost:3000

# Check Prometheus alerts
open http://localhost:9090/alerts
```

### 6. Start Frontend

```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with your VITE_STRIPE_PUBLISHABLE_KEY
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Kong API Gateway

Kong runs in **Postgres-backed mode** with full Admin API and Manager GUI support.

| Endpoint | URL | Purpose |
|----------|-----|---------|
| **Proxy** | `http://localhost:8000` | All client traffic goes here |
| **Admin API** | `http://localhost:8001` | Programmatic configuration |
| **Manager GUI** | `http://localhost:8002` | Visual configuration dashboard |

### Registered Routes

| Path | Upstream Service | Port |
|------|-----------------|------|
| `/drug/**` | drug_catalogue_service | 5001 |
| `/invoice/**` | invoice_service | 5003 |
| `/payments/**` | payment_service | 5004 |
| `/prescription/**` | prescription_service | 5005 |
| `/prescribe/**` | prescribe_medicine | 5007 |
| `/make_payment/**` | make_payment | 5008 |

### Adding Plugins

Plugins (rate limiting, authentication, logging) can be added via the Admin API or Manager GUI without restarting services:

```bash
# Example: Add rate limiting to drug catalogue
curl -X POST http://localhost:8001/services/drug-catalogue/plugins \
  --data "name=rate-limiting" \
  --data "config.minute=60" \
  --data "config.policy=local"
```

---

## Scaling Services

Docker Compose supports horizontal scaling. Kong load-balances across replicas automatically via Docker DNS.

```bash
# Scale drug service to 3 instances
docker compose up -d --scale drug_service=3

# Scale multiple services
docker compose up -d --scale drug_service=3 --scale invoice_service=2
```

> **Note:** `container_name` has been removed from scalable services to allow multiple instances. Only infrastructure services (Postgres, RabbitMQ) retain fixed names.

---

## Monitoring (Prometheus & Grafana)

Prometheus and Grafana are included in the Docker Compose stack and start automatically alongside all other services.

| Service | URL | Purpose |
|---------|-----|---------|
| **Prometheus** | `http://localhost:9090` | Metrics collection & alerting |
| **Grafana** | `http://localhost:3000` | Dashboards (no login required) |

### How It Works

```
Kong ──metrics──> Prometheus ──queries──> Grafana
(:8100/metrics)    (scrapes every 15s)     (dashboards + alerts)
```

1. Kong exposes metrics at port `8100` via the **Prometheus plugin** (enabled by `kong-setup.sh`)
2. Prometheus scrapes Kong every 15 seconds
3. Grafana reads from Prometheus and renders dashboards

> **Startup order:** Prometheus and Grafana start with `docker compose up` and begin collecting basic Kong metrics immediately. After running `./kong-setup.sh`, the Prometheus plugin is enabled and per-service metrics (request rates, latency, bandwidth) become available.

### Pre-configured Dashboard

Grafana ships with a **ClinicFlow - Kong Gateway Overview** dashboard that auto-loads on startup:

**Status Row:**
- Gateway status (UP/DOWN)
- Datastore reachable
- Total requests per second
- 5xx error rate
- Active connections

**Traffic:**
- Requests per second by service (line chart)
- Requests by HTTP status code (stacked bars: green=2xx, yellow=4xx, red=5xx)

**Latency:**
- Request latency by service (p50 / p95 / p99)
- Upstream (backend) latency by service (p50 / p95 / p99)

**Network & Health:**
- Bandwidth in/out per service
- Nginx connection states (active, reading, writing, waiting)
- Upstream health status table
- Drilldown table: requests by service and status code

### Prometheus Alerts

Pre-configured alert rules fire automatically when conditions are met. View status at `http://localhost:9090/alerts`.

| Alert | Condition | Severity |
|-------|-----------|----------|
| **HighErrorRate** | >5% of requests returning 5xx for 2 minutes | Critical |
| **ServiceDown** | Kong unreachable for 1 minute | Critical |
| **HighLatency** | p99 request latency >2s for 3 minutes | Warning |
| **HighUpstreamLatency** | p99 backend latency >1.5s for 3 minutes | Warning |
| **UpstreamUnhealthy** | Kong health check detects unhealthy upstream target | Critical |

### Useful Prometheus Queries

Run these in Prometheus (`http://localhost:9090/graph`) or as Grafana Explore queries:

```promql
# Total request rate across all services
sum(rate(kong_http_requests_total[5m]))

# Request rate per service
sum(rate(kong_http_requests_total[5m])) by (service)

# Error rate (5xx only)
sum(rate(kong_http_requests_total{code=~"5.."}[5m])) / sum(rate(kong_http_requests_total[5m]))

# p99 latency per service
histogram_quantile(0.99, sum(rate(kong_request_latency_ms_bucket[5m])) by (le, service))

# Bandwidth per service
sum(rate(kong_bandwidth_bytes[5m])) by (service, direction)
```

---

## Kubernetes Deployment

The `k8s/` directory contains manifests to deploy the full stack on Kubernetes with auto-scaling.

### Prerequisites

- **Docker Desktop** with Kubernetes enabled (Settings > Kubernetes > Enable)
- Docker images built locally (`docker compose build`)

### Quick Start

```bash
cd backend

# Deploy everything (builds images, creates namespace, deploys in order)
./k8s-setup.sh

# Tear down everything
./k8s-setup.sh teardown
```

The setup script handles the full deployment sequence:
1. Builds Docker images
2. Creates `clinicflow` namespace
3. Deploys secrets and infrastructure (Postgres, RabbitMQ)
4. Waits for databases to be healthy
5. Deploys atomic services (drug, invoice, prescription, payment)
6. Deploys composite services (prescribe medicine, make payment)
7. Deploys Kong API Gateway (DB-less mode with declarative config)
8. Deploys Prometheus and Grafana

### Architecture on K8s

| Component | K8s Resource | Replicas | Auto-scaling |
|-----------|-------------|----------|--------------|
| Drug Service | Deployment + HPA | 2 | 2-5 pods at 70% CPU |
| Invoice Service | Deployment + HPA | 2 | 2-5 pods at 70% CPU |
| Payment Service | Deployment + HPA | 2 | 2-5 pods at 70% CPU |
| Prescription Service | Deployment + HPA | 2 | 2-5 pods at 70% CPU |
| Prescribe Medicine | Deployment + HPA | 2 | 2-5 pods at 70% CPU |
| Make Payment | Deployment + HPA | 2 | 2-5 pods at 70% CPU |
| Kong | Deployment | 1 | LoadBalancer on :8000 |
| PostgreSQL | StatefulSet + PVC | 1 | 5Gi persistent volume |
| RabbitMQ | Deployment | 1 | - |
| Prometheus | Deployment | 1 | Scrapes Kong metrics |
| Grafana | Deployment + PVC | 1 | 2Gi persistent volume |

### K8s Manifest Files

```
k8s/
├── namespace.yml              # clinicflow namespace
├── secrets.yml                # DB + Stripe credentials
├── postgres.yml               # StatefulSet + PVC + init.sql ConfigMap
├── rabbitmq.yml               # Deployment + Service
├── drug-service.yml           # Deployment + Service + HPA
├── invoice-service.yml        # Deployment + Service + HPA
├── prescription-service.yml   # Deployment + Service + HPA
├── payment-service.yml        # Deployment + Service + HPA
├── prescribe-medicine.yml     # Deployment + Service + HPA
├── make-payment.yml           # Deployment + Service + HPA
├── kong.yml                   # Deployment + LoadBalancer + declarative config
├── prometheus.yml             # Deployment + Service + scrape config
└── grafana.yml                # Deployment + Service + PVC + datasource provisioning
```

### Useful K8s Commands

```bash
# Check all pods
kubectl get pods -n clinicflow

# Check auto-scaler status
kubectl get hpa -n clinicflow

# View logs for a service
kubectl logs -n clinicflow -l app=drug-service

# Scale manually
kubectl scale deployment drug-service -n clinicflow --replicas=5

# Describe a pod (debug startup issues)
kubectl describe pod -n clinicflow -l app=invoice-service

# Port-forward a service for local access
kubectl port-forward -n clinicflow svc/grafana 3000:3000

# Test Kong route
curl http://localhost:8000/drug
```

### Docker Compose vs Kubernetes

| | Docker Compose | Kubernetes |
|---|---|---|
| **Startup** | `docker compose up -d --build` + `./kong-setup.sh` | `./k8s-setup.sh` |
| **Scaling** | Manual: `--scale drug_service=3` | Auto: HPA scales on CPU usage |
| **Self-healing** | `restart: unless-stopped` | Auto-restarts + reschedules to healthy nodes |
| **Kong mode** | Postgres-backed (Admin API + GUI) | DB-less (declarative YAML config) |
| **Best for** | Development, demos | Production, auto-scaling |

---

## Database Reference

All services share a single PostgreSQL instance (`esd_db`) with isolated schemas.

| Schema | Service | Tables |
|--------|---------|--------|
| `drug_schema` | Drug Catalogue | `drug` |
| `prescription_schema` | Prescription | `prescription` |
| `invoice_schema` | Invoice | `invoices` |
| `payment_schema` | Payment | `payments` |

### Initialization

Database schemas and tables are created automatically on first startup via `backend/db/init.sql`. This script only runs when the PostgreSQL volume is first created.

To reset the database completely:

```bash
docker compose down -v
docker compose up -d --build
```

### Connecting Manually

```bash
docker exec -it esd-postgres psql -U clinic -d esd_db

# List schemas
\dn

# Query a table
SELECT * FROM drug_schema.drug;
```

---

## Environment Variables

### Shared Database Config (`backend/.env.postgres`)

| Variable | Description |
|----------|-------------|
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_PASSWORD` | PostgreSQL password |

### Per-Service Variables

| Variable | Used By | Description |
|----------|---------|-------------|
| `APP_ENV` | All | `docker` or `local` |
| `DB_HOST` | All DB services | `postgres` (Docker) or `localhost` (local) |
| `DB_PORT` | All DB services | `5432` |
| `DB_USER` / `DB_PASSWORD` | All DB services | Must match `.env.postgres` |
| `DB_NAME` | All DB services | `esd_db` |
| `DB_SCHEMA` | All DB services | Service-specific schema name |
| `STRIPE_SECRET_KEY` | Payment | Stripe test/live secret key |
| `STRIPE_WEBHOOK_SECRET` | Payment | Stripe webhook signing secret |
| `DRUG_CATALOGUE_URL` | Prescribe Medicine | `http://drug_service:5001` |
| `INVOICE_SERVICE_URL` | Prescribe Medicine, Make Payment | `http://invoice_service:5003` |
| `PRESCRIPTION_SERVICE_URL` | Prescribe Medicine | `http://prescription_service:5005` |
| `PAYMENT_SERVICE_URL` | Make Payment | `http://payment_service:5004` |
| `RABBITMQ_HOST` | Make Payment, Notification | `rabbitmq` (Docker) or `localhost` |
| `HTTP_TIMEOUT_SECONDS` | Composites | Timeout for inter-service calls (default: 8) |
| `TWILIO_ACCOUNT_SID` | Notification | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Notification | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | Notification | Twilio sender number |

---

## Frontend

### Overview

The frontend is a Vue 3 single-page application built with Vite and Tailwind CSS. It communicates with backend microservices through Kong API Gateway (port 8000) and directly with OutSystems REST APIs for clinical records and patient management.

### Tech Stack

| Technology | Purpose |
|-----------|---------|
| Vue 3 (Composition API) | Reactive UI framework |
| Vite | Build tool and dev server |
| Vue Router | Client-side routing |
| Tailwind CSS | Utility-first styling |
| Axios | HTTP client for API calls |
| Lucide Vue Next | Icon library |
| Stripe.js | Payment card element |

### Architecture

The frontend is organized into four layers:

```
frontend/src/
├── api/              # API endpoint configuration and service functions
│   ├── endpoints.js  # All API URLs (Kong + OutSystems)
│   ├── drugs.js      # Drug catalogue CRUD
│   ├── records.js    # Clinical records (OutSystems)
│   ├── patients.js   # Patient management (OutSystems)
│   ├── invoices.js   # Invoice service
│   ├── payment.js    # Payment orchestration
│   └── prescriptions.js  # Prescription lookups
├── composables/      # Reactive state + business logic (Vue composables)
│   ├── useInventory.js       # Drug inventory state and CRUD
│   ├── useRecords.js         # Clinical records with patient enrichment
│   ├── useConsultation.js    # Consultation form and drug selection
│   ├── usePatients.js        # Patient list and registration
│   ├── usePatientHistory.js  # Patient history with prescriptions
│   ├── useInvoices.js        # Invoice data with record/patient joins
│   ├── usePayment.js         # Stripe payment flow
│   ├── useToast.js           # Toast notifications
│   └── useOutsystemsSync.js  # Sync indicator for OutSystems calls
├── components/       # UI components (views + modals)
│   ├── AppSidebar.vue             # Navigation sidebar
│   ├── AppHeader.vue              # Page header with refresh
│   ├── ToastContainer.vue         # Toast notification overlay
│   ├── InventoryView.vue          # Drug inventory table with CRUD
│   ├── ConsultationView.vue       # Create consultation form
│   ├── PastConsultationsView.vue  # Consultation records with filters
│   ├── PatientHistoryView.vue     # Patient record + prescription lookup
│   ├── PatientsView.vue           # All patients table
│   ├── PaymentsView.vue           # Billing table + payment wizard
│   ├── AddDrugModal.vue           # Add drug modal
│   ├── EditDrugModal.vue          # Edit drug modal
│   ├── DeleteDrugModal.vue        # Delete confirmation modal
│   ├── PatientRegistrationModal.vue  # Register patient modal
│   └── PatientDetailsModal.vue    # Patient details modal
├── views/            # Full-screen pages (no sidebar layout)
│   ├── ConsultationReview.vue  # Review + add medication + confirm
│   ├── PaymentSuccess.vue      # Payment success page
│   └── ...
├── utils/            # Utility functions
│   └── normalizers.js  # Data normalization for API responses
└── router/
    └── index.js      # Route definitions
```

### Routes

| Path | Page | Description |
|------|------|-------------|
| `/` | Inventory | Drug inventory with add/edit/delete |
| `/consultation` | Create Consultation | Enter patient ID and visit notes |
| `/consultation/review` | Consultation Review | Add medication, review, and confirm submission |
| `/past-consultations` | Past Consultations | All consultation records with open/closed filter |
| `/patient-history` | Patient History | Lookup records and prescriptions by patient ID |
| `/patients` | All Patients | Searchable patient list with details |
| `/payments` | Payments | Billing table, invoice list, and Stripe payment wizard |
| `/payment-success` | Payment Success | Payment confirmation page |

### API Routing

The frontend routes requests to two backends:

| Destination | Services | Base URL |
|-------------|----------|----------|
| **Kong Gateway** | Drug Catalogue, Invoice, Payment, Prescription, Prescribe Medicine, Make Payment | `http://localhost:8000` (configurable via `VITE_KONG_BASE`) |
| **OutSystems** | Clinical Records (RecordsAPI), Patient Management (PatientAPI), Consultation (ConsultationAPI) | Direct HTTPS to `outsystemscloud.com` |

### Key Features

- **Patient Verification** — Validates patient exists via OutSystems PatientAPI before submitting consultations
- **Drug Catalogue on Review Page** — Add medication directly on the consultation review page before confirming
- **Invoice-Based Payments** — Fetches invoices from the invoice service, initiates Stripe PaymentIntents, confirms with card element, and polls for backend confirmation
- **Invoice Status Cross-Reference** — Records show as "Closed" when their linked invoice is paid, even if OutSystems hasn't updated
- **Pagination** — All list views (past consultations, patients, patient history, billing) paginate at 10 items per page
- **Status Filters** — Past consultations filter by Open/Closed, billing table filters by Paid/Draft/Pending/Failed
- **Toast Notifications** — Success/error feedback for CRUD operations
- **Syncing Indicator** — Shows when OutSystems API calls are in progress

### Frontend Setup

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

#### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `frontend/.env`:

```env
VITE_KONG_BASE=http://localhost:8000
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
```

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_KONG_BASE` | Kong API Gateway URL | `http://localhost:8000` |
| `VITE_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key for card element | (required) |
| `VITE_CONSULTATION_BASE` | Override ConsultationAPI URL | OutSystems URL |
| `VITE_PRESCRIPTION_BY_PATIENT_BASE` | Override Prescription service URL | Kong `/prescription` |
| `VITE_PRESCRIBE_MEDICINE_BASE` | Override Prescribe Medicine URL | Kong `/prescribe` |

#### 3. Start Development Server

```bash
npm run dev
```

The frontend runs at `http://localhost:5173`.

#### 4. Build for Production

```bash
npm run build
```

Output is written to `frontend/dist/`.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `connection refused` to database | Wait for Postgres healthcheck to pass, or check `DB_HOST`/`DB_USER` in `.env` |
| Schema does not exist | Run `docker compose down -v && docker compose up -d --build` to reinitialize |
| `EXTERNAL_ERROR` from composite | Check that all downstream services are running with `docker compose ps` |
| `DEPENDENCY_UNREACHABLE` | Verify service URLs in `.env` use Docker hostnames (e.g., `drug_service` not `localhost`) |
| Kong returns 404 | Run `./kong-setup.sh` to register routes |
| Stripe key errors | Ensure `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` are set in `payment_service/.env` |
| Port conflict on scale | Ensure `container_name` is not set for the service you're scaling |
| Invoice enum error (`DRAFT`) | Run: `docker exec esd-postgres psql -U clinic -d esd_db -c "ALTER TYPE invoice_schema.invoice_status ADD VALUE IF NOT EXISTS 'DRAFT';"` |
| RabbitMQ connection refused | Wait for RabbitMQ healthcheck; check `RABBITMQ_HOST` in `.env` |
| CORS errors in browser | Run `./kong-setup.sh` to enable CORS plugin; ensure `X-Internal-Api-Key` is in allowed headers |
| Frontend shows "Unknown patient" | Records from OutSystems lack patient names; the frontend joins patient data client-side — ensure patients are loaded |
| Invoice stuck in `payment_pending` | Stripe webhook didn't fire (no `stripe listen` running); the frontend calls `/payment-events` directly as fallback |
| Twilio SMS 401 error | Check `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` in `.env.docker`; verify at Twilio console |
| `STRIPE_SECRET_KEY` empty in container | Remove `${STRIPE_SECRET_KEY:-}` overrides from `docker-compose.yml`; use `env_file` values from `.env.docker` |
| Consultation 500 with empty body | Patient does not exist on OutSystems; frontend validates before submission |

### Useful Commands

```bash
# View logs for a specific service
docker compose logs -f drug_service

# Restart a single service
docker compose restart invoice_service

# Rebuild and restart one service
docker compose up -d --build prescribe_medicine

# Check Kong registered routes
curl http://localhost:8001/routes | python3 -m json.tool

# Check Kong upstreams and targets
curl http://localhost:8001/upstreams | python3 -m json.tool
```

---

## Project Structure

```
ESD_G4T2/
├── backend/
│   ├── docker-compose.yml          # Full stack orchestration (12 containers)
│   ├── kong-setup.sh               # Kong route + Prometheus plugin setup
│   ├── k8s-setup.sh                # One-command Kubernetes deployment
│   ├── kong.yml                    # Kong declarative config (reference)
│   ├── prometheus.yml              # Prometheus scrape config
│   ├── prometheus-alerts.yml       # Alert rules (error rate, latency, health)
│   ├── .env.postgres               # Database credentials
│   ├── db/
│   │   └── init.sql                # Schema + table initialization
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   └── kong-overview.json  # Pre-built Kong monitoring dashboard
│   │   └── provisioning/
│   │       ├── dashboards/
│   │       │   └── dashboards.yml  # Dashboard auto-provisioning config
│   │       └── datasources/
│   │           └── datasource.yml  # Prometheus datasource config
│   ├── k8s/                        # Kubernetes manifests
│   │   ├── namespace.yml
│   │   ├── secrets.yml
│   │   ├── postgres.yml
│   │   ├── rabbitmq.yml
│   │   ├── drug-service.yml
│   │   ├── invoice-service.yml
│   │   ├── prescription-service.yml
│   │   ├── payment-service.yml
│   │   ├── prescribe-medicine.yml
│   │   ├── make-payment.yml
│   │   ├── kong.yml
│   │   ├── prometheus.yml
│   │   └── grafana.yml
│   ├── requirements/               # Shared dependency files
│   │   ├── base.txt                # FastAPI stack (shared)
│   │   ├── invoice.txt
│   │   ├── drug_catalogue.txt
│   │   ├── prescription.txt
│   │   ├── payment.txt
│   │   ├── prescribe_medicine.txt
│   │   └── make_payment.txt
│   ├── services/
│   │   ├── invoice_service/        # FastAPI — invoice CRUD + status machine
│   │   ├── drug_catalogue_service/ # FastAPI — drug inventory management
│   │   ├── prescription_service/   # FastAPI — prescription records
│   │   ├── payment_service/        # FastAPI — Stripe payment processing
│   │   └── notification_service/   # Async — RabbitMQ consumer + Twilio SMS
│   └── composites/
│       ├── prescribe_medicine/     # Flask — prescription workflow orchestrator
│       └── make_payment/           # Flask — payment workflow orchestrator
└── frontend/                       # Vue 3 + Vite SPA
    ├── .env                        # Environment variables (gitignored)
    ├── .env.example                # Template for environment setup
    ├── vite.config.js              # Vite configuration
    ├── index.html                  # Entry HTML
    ├── package.json                # Dependencies
    └── src/
        ├── App.vue                 # Root layout (sidebar + router-view)
        ├── main.js                 # Vue app entry point
        ├── router/index.js         # Route definitions
        ├── api/                    # API endpoint configs and service functions
        ├── composables/            # Reactive state management (Vue composables)
        ├── components/             # UI components (views + modals)
        ├── views/                  # Full-screen pages
        └── utils/                  # Data normalizers and helpers
```
