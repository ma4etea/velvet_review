from typing import TypeVar, Generic

from pydantic import BaseModel as BaseSchema

SchemaType = TypeVar("SchemaType", bound=BaseSchema)


class DataMapper(Generic[SchemaType]):
    schema: type[SchemaType]

    @classmethod
    def to_domain(cls, json: str) -> SchemaType:
        """Конвертирует JSON-строку в DTO"""
        return cls.schema.model_validate_json(json)

    @classmethod
    def to_cache(cls, schema: SchemaType) -> str:
        """Конвертирует DTO обратно в JSON"""
        return schema.model_dump_json()
