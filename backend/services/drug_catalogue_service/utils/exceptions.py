class AppError(Exception):
    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class ValidationError(AppError):
    status_code = 400


class ConflictError(AppError):
    status_code = 409