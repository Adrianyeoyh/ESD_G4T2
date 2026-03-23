import re
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config.drug_db import Base, engine
from app.config.settings import DB_SCHEMA
from app.routes.drug_routes import router
from utils.exceptions import AppError

# Ensure model metadata is registered before create_all runs.
from app.models.drug_model import Drug


logger = logging.getLogger(__name__)


def _validated_schema_name() -> str:
    """Validate schema identifier before using it in DDL."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", DB_SCHEMA):
        raise RuntimeError(f"Invalid DB_SCHEMA value: {DB_SCHEMA!r}")
    return DB_SCHEMA


SCHEMA_NAME = _validated_schema_name()
TABLE_NAME = "drug"


@asynccontextmanager
async def lifespan(_: FastAPI):
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA_NAME}"'))

    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        apply_migrations(conn)

    yield


# Initialize FastAPI
app = FastAPI(
    title="Drug Catalogue Service",
    description="Atomic microservice for managing drug inventory",
    lifespan=lifespan,
)


@app.exception_handler(AppError)
def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(SQLAlchemyError)
def handle_sqlalchemy_error(_: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("Database error occurred", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Database error occurred"})


def check_constraint_exists(conn, constraint_name: str) -> bool:
    """Check if a constraint already exists on the drug table."""
    stmt = text(
        """
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_schema = :schema_name
          AND table_name = :table_name
          AND constraint_name = :constraint_name
        """
    )
    result = conn.execute(
        stmt,
        {
            "schema_name": SCHEMA_NAME,
            "table_name": TABLE_NAME,
            "constraint_name": constraint_name,
        },
    )
    return result.fetchone() is not None


def check_index_exists(conn, index_name: str) -> bool:
    """Check if an index already exists on the drug table."""
    stmt = text(
        """
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = :schema_name
          AND tablename = :table_name
          AND indexname = :index_name
        """
    )
    result = conn.execute(
        stmt,
        {
            "schema_name": SCHEMA_NAME,
            "table_name": TABLE_NAME,
            "index_name": index_name,
        },
    )
    return result.fetchone() is not None


def drug_name_needs_type_migration(conn) -> bool:
    """Return True when drugName is not already VARCHAR(255)."""
    stmt = text(
        """
        SELECT data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = :schema_name
          AND table_name = :table_name
          AND column_name = :column_name
        """
    )
    row = conn.execute(
        stmt,
        {
            "schema_name": SCHEMA_NAME,
            "table_name": TABLE_NAME,
            "column_name": "drugName",
        },
    ).fetchone()

    # If column metadata is missing, let the ALTER run and fail loudly.
    if row is None:
        return True

    data_type, max_length = row
    return not (data_type == "character varying" and max_length == 255)


def apply_migrations(conn) -> None:
    """Apply database schema migrations."""
    table_ref = f'"{SCHEMA_NAME}"."{TABLE_NAME}"'

    if not check_constraint_exists(conn, "uq_drug_name"):
        try:
            conn.execute(
                text(
                    f"""
                    ALTER TABLE {table_ref}
                    ADD CONSTRAINT uq_drug_name UNIQUE ("drugName")
                    """
                )
            )
        except SQLAlchemyError:
            # Ignore duplicate-object race if another instance created it first.
            if check_constraint_exists(conn, "uq_drug_name"):
                logger.info("Constraint uq_drug_name already exists; skipping")
            else:
                logger.exception("Failed applying uq_drug_name migration")
                raise

    if not check_constraint_exists(conn, "ck_quantity_non_negative"):
        try:
            conn.execute(
                text(
                    f"""
                    ALTER TABLE {table_ref}
                    ADD CONSTRAINT ck_quantity_non_negative CHECK (quantity >= 0)
                    """
                )
            )
        except SQLAlchemyError:
            if check_constraint_exists(conn, "ck_quantity_non_negative"):
                logger.info("Constraint ck_quantity_non_negative already exists; skipping")
            else:
                logger.exception("Failed applying ck_quantity_non_negative migration")
                raise

    if not check_constraint_exists(conn, "ck_price_positive"):
        try:
            conn.execute(
                text(
                    f"""
                    ALTER TABLE {table_ref}
                    ADD CONSTRAINT ck_price_positive CHECK (price > 0)
                    """
                )
            )
        except SQLAlchemyError:
            if check_constraint_exists(conn, "ck_price_positive"):
                logger.info("Constraint ck_price_positive already exists; skipping")
            else:
                logger.exception("Failed applying ck_price_positive migration")
                raise

    if drug_name_needs_type_migration(conn):
        try:
            conn.execute(
                text(
                    f"""
                    ALTER TABLE {table_ref}
                    ALTER COLUMN "drugName" TYPE VARCHAR(255)
                    """
                )
            )
        except SQLAlchemyError:
            logger.exception("Failed applying drugName column migration")
            raise
    else:
        logger.info("Column drugName already VARCHAR(255); skipping type migration")

    if not check_index_exists(conn, "ix_drug_name_ci"):
        try:
            conn.execute(
                text(
                    f"""
                    CREATE INDEX ix_drug_name_ci
                    ON {table_ref} (LOWER("drugName"))
                    """
                )
            )
        except SQLAlchemyError:
            if check_index_exists(conn, "ix_drug_name_ci"):
                logger.info("Index ix_drug_name_ci already exists; skipping")
            else:
                logger.exception("Failed applying ix_drug_name_ci migration")
                raise


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)