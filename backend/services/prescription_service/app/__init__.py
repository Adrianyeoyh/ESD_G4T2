from fastapi import FastAPI, Request
# from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.routers.prescription_router import router as prescription_router
from app.config.prescription_db import Base, engine
from app.models import prescription_model  # noqa: F401 - registers model on Base
from utils.exceptions import AppError

def create_app() -> FastAPI:
    app = FastAPI(
        title="Prescription Service",
        version="1.0.0",
        description="Atomic microservice for assigning patient prescriptions",
    )

    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "data": None, "error": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(request: Request, exc: RequestValidationError):
        details = []
        for err in exc.errors():
            details.append(
                {
                    "loc": err.get("loc"),
                    "msg": err.get("msg"),
                    "type": err.get("type"),
                }
            )

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "data": None,
                "error": "Validation failed",
                "details": details,
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"success": False, "data": None, "error": "Internal server error"},
        )

    # ── Router registration ─────────────────────────────────────────────────
    app.include_router(prescription_router)

    # ── DB schema management ────────────────────────────────────────────────
    # Safe for dev: create_all is idempotent (skips existing tables).
    Base.metadata.create_all(bind=engine)

    return app


app = create_app()
