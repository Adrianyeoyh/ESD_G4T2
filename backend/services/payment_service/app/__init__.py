from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers.payment_router import router as payment_router, health_router
from utils.exceptions import AppError


def create_app() -> FastAPI:
    app = FastAPI(
        title="Payment Service API",
        version="1.0.0",
        description="Atomic microservice for payment processing",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
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

    app.include_router(payment_router)
    app.include_router(health_router)
    return app


app = create_app()
