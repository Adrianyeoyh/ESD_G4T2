from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers.record_router import router as record_router
from utils.exceptions import AppError


def create_app() -> FastAPI:
    app = FastAPI(
        title="Clinical Record Service",
        version="1.0.0",
        description="Atomic microservice for managing clinical records",
    )

    # ✅ Custom App Error Handler
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "data": None, "error": exc.message},
        )

    # ✅ Generic Error Handler
    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"success": False, "data": None, "error": "Internal server error"},
        )

    # ✅ Register Record Router
    app.include_router(record_router)

    return app


app = create_app()