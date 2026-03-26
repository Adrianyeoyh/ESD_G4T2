class AppError(Exception):
    """Base application error with HTTP status code"""
    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    """404 - Resource not found"""
    status_code = 404


class ValidationError(AppError):
    """400 - Request validation failed"""
    status_code = 400


class ConflictError(AppError):
    """409 - Resource state conflict (e.g., insufficient stock)"""
    status_code = 409


class ServiceUnavailableError(AppError):
    """503 - Downstream service unavailable or timeout"""
    status_code = 503


class InternalServerError(AppError):
    """500 - Internal server error"""
    status_code = 500