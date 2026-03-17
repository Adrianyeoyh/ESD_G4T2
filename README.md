# ESD_G4T2


# Backend README

## Starting the local PostgreSQL database

This backend uses a **local Dockerized PostgreSQL database** for development.

### Prerequisites
- Docker Desktop installed
- Docker Desktop running

### Start the database
From the project root, run:

```bash
./backend/scripts/start-db.sh
```

This script starts a PostgreSQL container named `esd-postgres`.

Current local setup:
- **Host port:** `5432`
- **Container port:** `5432`
- **Database name:** `esd_db`
- **Username:** `clinic`
- **Password:** `clinic`

### What the script does
The script:
1. removes any old `esd-postgres` container with the same name
2. starts a new PostgreSQL container
3. mounts the persistent Docker volume for database storage
4. mounts `backend/db/init.sql` into `/docker-entrypoint-initdb.d/init.sql`

On the **first startup of a fresh database volume**, PostgreSQL will automatically run `init.sql` to create the required schemas, such as:
- `patient_schema`
- `records_schema`
- `drug_schema`
- `prescription_schema`
- `invoice_schema`

## Verify that the database is running
Run:

```bash
docker ps
```

You should see a container named `esd-postgres` with a port mapping like:

```text
0.0.0.0:5433->5432/tcp
```

You can also check the logs:

```bash
docker logs esd-postgres
```

A healthy startup will include a message similar to:

```text
database system is ready to accept connections
```

## Database connection string
If running the Flask microservice **locally on your machine** rather than inside Docker, use:

```env
DATABASE_URL=postgresql+psycopg2://esd_user:esd_pass@localhost:5433/esd_db
```

## Connect to the database manually
To open a Postgres shell inside the container:

```bash
docker exec -it esd-postgres psql -U esd_user -d esd_db
```

Inside `psql`, list schemas with:

```sql
\dn
```

Exit with:

```sql
\q
```

## Stop the database
To stop only this database container:

```bash
docker stop esd-postgres
```

To start it again later:

```bash
docker start esd-postgres
```

## Recreate the database from scratch
If you need a completely fresh database:

```bash
docker rm -f esd-postgres
docker volume rm esd_pgdata
./backend/scripts/start-db.sh
```

This will delete all existing local database data in the `esd_pgdata` volume.

## Notes
- `init.sql` only runs automatically when PostgreSQL initializes a **fresh** data directory.
- If the volume already exists, PostgreSQL will not rerun `init.sql` automatically.
- If you change schema setup later, either run SQL manually or recreate the volume.
