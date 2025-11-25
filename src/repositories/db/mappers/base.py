from pydantic import BaseModel as BaseSchema
from typing import TypeVar, Generic

from src.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
SchemaType = TypeVar("SchemaType", bound=BaseSchema)


class DataMapper(Generic[ModelType, SchemaType]):
    model: type[ModelType]
    schema: type[SchemaType]

    @classmethod
    def to_domain(cls, model: ModelType, exclude_lazy: bool = False) -> SchemaType:
        """
        :param model: Орм модель.
        :param exclude_lazy: Отключить ленивую загрузку если поля не загружены в орм модели.
        :return: DTO
        """
        if exclude_lazy:
            data = model.__dict__
            return cls.schema.model_validate(data)

        return cls.schema.model_validate(model, from_attributes=True)

    @classmethod
    def to_persist(cls, schema: SchemaType, exclude_unset: bool = False) -> ModelType:
        return cls.model(**schema.model_dump(exclude_unset=exclude_unset))
