from src.routers.http_exceptions.base import VelvetHTTPException


class BadRequestHTTPException(VelvetHTTPException):
    status_code = 400
    details = "Bad request"


class UnitBelongAnotherStoreHTTPException(BadRequestHTTPException):
    details = "Some unit_ids belong to another store"
