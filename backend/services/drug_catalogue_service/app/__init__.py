
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, APIRouter, Depends, status  
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.routers.drug_router import router as drug_router
from app.config.drug_db import Base, engine
from app.models import drug_model  # noqa: F401 — registers model on Base
from utils.exceptions import AppError

def create_app() -> FastAPI:
    app = FastAPI(
        title="Drug Catalogue Service",
        version="1.0.0",
        description="Atomic microservice for managing drug inventory",
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

    # ── Router registration ─────────────────────────────────────────────────
    app.include_router(drug_router)

    # ── DB schema management ────────────────────────────────────────────────
    # Safe for dev: create_all is idempotent (skips existing tables).
    Base.metadata.create_all(bind=engine)

    return app


app = create_app()
