from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers.invoice_router import router as invoice_router
from app.config.db import Base, engine
from utils.exceptions import AppError


def create_app() -> FastAPI:
    app = FastAPI(
        title="Invoice Service API",
        version="1.0.0",
        description="Atomic microservice for invoice management",
    )

    # ── Global exception handlers ───────────────────────────────────────────
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
    app.include_router(invoice_router)

    # ── Ensure DB tables exist ──────────────────────────────────────────────
    Base.metadata.create_all(bind=engine)

    return app


app = create_app()