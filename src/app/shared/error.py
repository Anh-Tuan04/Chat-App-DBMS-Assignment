"""Application error classes."""

from __future__ import annotations


class AppError(Exception):
    """Base class for all application errors."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BadRequest(AppError):
    def __init__(self, message: str = "Bad request"):
        super().__init__(message, status_code=400)


class Unauthorized(AppError):
    def __init__(self, message: str = "Not logged in"):
        super().__init__(message, status_code=401)


class Forbidden(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class NotFound(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class Conflict(AppError):
    def __init__(self, message: str = "Conflict"):
        super().__init__(message, status_code=409)


class AlreadyExists(Conflict):
    def __init__(self, message: str = "Already exists"):
        super().__init__(message)


class Blocked(AppError):
    def __init__(self, message: str = "User is blocked"):
        super().__init__(message, status_code=404)


class Unavailable(AppError):
    def __init__(self, message: str = "Service unavailable"):
        super().__init__(message, status_code=503)

