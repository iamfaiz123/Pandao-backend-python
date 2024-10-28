from enum import Enum

from fastapi import HTTPException


class ApiError(Exception):
    def __init__(self, cause, status):
        self.cause = cause
        self.status = status
        self.http_error = HTTPException(status_code=status, detail=cause)

    def as_http_response(self):
        raise self.http_error

    def __str__(self):
        return f"{self.cause}"

    @staticmethod
    def internal_server_error(message: str):
        if str:
            return ApiError(message, 500)
        else:
            return ApiError("Internal Server Error", 500)

    @staticmethod
    def unauthorized():
        return ApiError("unauthorized", 401)
