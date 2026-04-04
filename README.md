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
- [Kong API Gateway](#kong-api-gateway)
- [Scaling Services](#scaling-services)
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

#### 2b. Service Environment Files

Each service needs a `.env` file. Copy from examples and fill in values:

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

#### 2c. Stripe Keys

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

### 4. Configure Kong Routes

After all containers are healthy, run the setup script:

```bash
./kong-setup.sh
```

This registers upstreams, services, and routes in Kong via the Admin API.

### 5. Verify

```bash
# Check all containers are running
docker compose ps

# Test through Kong
curl http://localhost:8000/drug

# Access Kong Manager GUI
open http://localhost:8002
```

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
| `/drug/**` | drug_service | 5001 |
| `/payments/**` | payment_service | 5004 |
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
│   ├── docker-compose.yml          # Full stack orchestration
│   ├── kong-setup.sh               # Kong route registration script
│   ├── kong.yml                    # Kong declarative config (reference)
│   ├── .env.postgres               # Database credentials
│   ├── db/
│   │   └── init.sql                # Schema + table initialization
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
└── frontend/                       # (In development)
```
