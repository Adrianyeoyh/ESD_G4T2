# ESD_G4T2 — Backend Setup Guide

This guide covers how to get the full backend running locally using **Docker Compose**. All services (Postgres, Invoice Service, Payment Service) are orchestrated together.

---

## Prerequisites

| Tool | Purpose |
|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Run all containers |
| Git | Clone the repo |

Make sure **Docker Desktop is running** before proceeding.

---

## Directory Structure

```
backend/
├── docker-compose.yml           # Orchestrates all services
├── .env.postgres                # PostgreSQL credentials (you create this)
├── .env.postgres.example        # Template for above
├── db/                          # SQL init scripts (run on first DB boot)
├── services/
│   ├── invoice_service/
│   │   ├── .env                 # Invoice service env vars (you create this)
│   │   └── .env.example         # Template for above
│   └── payment_service/
│       ├── .env                 # Payment service env vars (you create this)
│       └── .env.example         # Template for above
```

---

## Step 1 — Set Up Environment Variables

The backend uses `.env` files that are **not committed to Git**. You need to create them from the provided `.example` templates.

### 1a. PostgreSQL credentials

```bash
cp backend/.env.postgres.example backend/.env.postgres
```

Then open `backend/.env.postgres` and fill in your values:

```env
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
```

> **Note:** These credentials are used both by the Postgres container and referenced by the individual services. Keep them consistent.

---

### 1b. Invoice Service

```bash
cp backend/services/invoice_service/.env.example backend/services/invoice_service/.env
```

Open `backend/services/invoice_service/.env`:

```env
APP_ENV=docker          # Use 'docker' when running via Docker Compose, 'local' for local dev
DB_HOST=postgres        # Must match the service name in docker-compose.yml
DB_PORT=5432
DB_USER=your_db_user    # Same as POSTGRES_USER in .env.postgres
DB_PASSWORD=your_db_password  # Same as POSTGRES_PASSWORD in .env.postgres
DB_NAME=esd_db
DB_SCHEMA=invoice_schema
```

> **`APP_ENV` values explained:**
> - `docker` — service is running inside Docker Compose; uses container networking (e.g. `DB_HOST=postgres`)
> - `local` — service is running on your machine directly; `DB_HOST` should be `localhost`

---

### 1c. Payment Service

```bash
cp backend/services/payment_service/.env.example backend/services/payment_service/.env
```

Open `backend/services/payment_service/.env`:

```env
APP_ENV=docker
DB_HOST=postgres
DB_PORT=5432
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=esd_db
DB_SCHEMA=payment_schema

STRIPE_SECRET_KEY=sk_test_...          # Your Stripe secret key (from Stripe Dashboard)
STRIPE_WEBHOOK_SECRET=whsec_...        # Your Stripe webhook signing secret
BILLING_SERVICE_URL=http://localhost:5005  # URL for billing service (adjust if needed)
```

> **Getting Stripe keys:**
> 1. Go to [https://dashboard.stripe.com/test/apikeys](https://dashboard.stripe.com/test/apikeys)
> 2. Copy the **Secret key** (`sk_test_...`) into `STRIPE_SECRET_KEY`
> 3. For webhooks, go to **Developers → Webhooks** and grab the signing secret (`whsec_...`) into `STRIPE_WEBHOOK_SECRET`

---

## Step 2 — Build and Start All Services

From the **`backend/`** directory:

```bash
cd backend
docker compose up --build
```

This will:
1. Pull the `postgres:16` image and start the database
2. Wait for Postgres to pass its healthcheck before starting services
3. Build and start `invoice_service` (port **5003**)
4. Build and start `payment_service` (port **5004**)

On the **first startup ever**, Postgres will automatically run all `.sql` files in `backend/db/` to initialize schemas (`invoice_schema`, `payment_schema`, etc.).

---

## Step 3 — Verify Everything Is Running

```bash
docker ps
```

You should see three containers:

```
CONTAINER ID   NAME               PORTS
...            esd-postgres       0.0.0.0:5432->5432/tcp
...            invoice_service    0.0.0.0:5003->5003/tcp
...            payment_service    0.0.0.0:5004->5004/tcp
```

Check logs for a specific service:

```bash
docker compose logs invoice_service
docker compose logs payment_service
docker compose logs postgres
```

---

## Service Endpoints

| Service | Port | Base URL |
|---|---|---|
| Invoice Service | 5003 | `http://localhost:5003` |
| Payment Service | 5004 | `http://localhost:5004` |

---

## Stopping the Stack

```bash
docker compose down
```

To also delete the database volume (⚠️ destroys all data):

```bash
docker compose down -v
```

---

## Rebuilding After Code Changes

If you change service code or dependencies:

```bash
docker compose up --build
```

---

## Connecting to the Database Manually

```bash
docker exec -it esd-postgres psql -U your_db_user -d esd_db
```

Inside `psql`:

```sql
-- List all schemas
\dn

-- Switch to invoice schema
SET search_path TO invoice_schema;

-- List tables
\dt

-- Exit
\q
```

---

## Recreating the Database from Scratch

If you need a completely fresh database (re-runs `init.sql`):

```bash
docker compose down -v
docker compose up --build
```

> **Why `-v`?** The SQL init scripts in `backend/db/` only run when PostgreSQL initializes a **brand new** volume. Removing the volume forces a fresh init.

---

## Running Services Locally (Without Docker Compose)

If you prefer to run a service directly on your machine during development:

1. Start **only** the database container:
   ```bash
   docker compose up postgres
   ```

2. In the service's `.env`, set:
   ```env
   APP_ENV=local
   DB_HOST=localhost
   DB_PORT=5432
   ```

3. Install dependencies and run:
   ```bash
   cd backend/services/invoice_service
   pip install -r ../../requirements/invoice.txt
   python run.py
   ```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `connection refused` on DB | Make sure Postgres healthcheck passed — wait a few seconds and retry |
| Service can't reach `postgres` host | Ensure `APP_ENV=docker` and `DB_HOST=postgres` in `.env` |
| `STRIPE_SECRET_KEY` missing error | Fill in Stripe keys in `payment_service/.env` |
| Schema not created | Run `docker compose down -v && docker compose up --build` to reset DB |
| Port already in use | Stop any local conflicting processes on ports 5432, 5003, or 5004 |
