from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import stripe

from app.routers.payment_router import router as payment_router, health_router, legacy_router
from app.config.db import Base, engine
from app.models import payment_model  # noqa: F401 â€” registers model on Base
from utils.exceptions import AppError


def create_app() -> FastAPI:
    app = FastAPI(
        title="Payment Service API",
        version="1.0.0",
        description="Atomic microservice for payments and Stripe integration",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # â”€â”€ Global exception handlers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "data": None, "error": exc.message},
        )

    @app.exception_handler(stripe.error.SignatureVerificationError)
    async def stripe_signature_handler(request: Request, exc: stripe.error.SignatureVerificationError):
        return JSONResponse(
            status_code=400,
            content={"success": False, "data": None, "error": "Invalid Stripe signature"},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"success": False, "data": None, "error": "Internal server error"},
        )

    # â”€â”€ Router registration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    app.include_router(payment_router)
    app.include_router(legacy_router)
    app.include_router(health_router)

    # â”€â”€ DB schema management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Safe for dev: create_all is idempotent (skips existing tables).
    Base.metadata.create_all(bind=engine)

    return app


app = create_app()

