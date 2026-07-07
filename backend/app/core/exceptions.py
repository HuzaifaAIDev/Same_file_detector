"""Application-level exceptions, kept separate from framework exceptions
so services/repositories don't need to depend on FastAPI."""


class AppError(Exception):
    """Base class for expected, handled application errors."""

    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class ValidationAppError(AppError):
    status_code = 422


class AuthError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class RateLimitError(AppError):
    status_code = 429
