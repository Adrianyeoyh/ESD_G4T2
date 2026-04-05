from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config.drug_db import Base, engine
from app.config.settings import DB_SCHEMA
from app.models import drug_model  # noqa: F401 - registers model on Base
from app.routers.drug_router import router as drug_router
from utils.exceptions import AppError


def create_app() -> FastAPI:
    app = FastAPI(
        title="Drug Catalogue Service",
        version="1.0.0",
        description="Atomic microservice for managing drug inventory",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "data": None, "error": exc.message},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"success": False, "data": None, "error": "Internal server error"},
        )

    app.include_router(drug_router)

    # Safe for dev: create_all is idempotent (skips existing tables).
    Base.metadata.create_all(bind=engine)

    # Backfill new optional columns for local databases that already had the table.
    with engine.begin() as conn:
        conn.execute(
            text(f'ALTER TABLE "{DB_SCHEMA}"."drug" ADD COLUMN IF NOT EXISTS "purpose" VARCHAR(255)')
        )
        conn.execute(
            text(
                f'ALTER TABLE "{DB_SCHEMA}"."drug" ADD COLUMN IF NOT EXISTS "recommendedDosage" VARCHAR(255)'
            )
        )
        conn.execute(
            text(f'ALTER TABLE "{DB_SCHEMA}"."drug" ADD COLUMN IF NOT EXISTS "remarks" VARCHAR(500)')
        )

    return app


app = create_app()
