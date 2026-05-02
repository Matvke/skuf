from __future__ import annotations

from pydantic import BaseModel, Field

from extractors.models import Entity
from scheams.meta_schemas import ActionInfo


class ProcessingBody(BaseModel):
    """Тело запроса для обработки текста."""

    text: str = Field(
        description="Входной текст, в котором нужно найти сущности",
        examples=["Паспорт 4507 123456, ИНН 7712345678, phone +7 999 123-45-67"],
    )


class EntitiesResponse(BaseModel):
    """Результат детекции: список найденных сущностей."""

    entities: list[Entity] = Field(
        default_factory=list,
        description="Найденные сущности (отсортированы по позиции в тексте)",
    )


class AnonymizedTextResponse(BaseModel):
    """Результат анонимизации: текст с заменёнными сущностями."""

    text: str = Field(description="Анонимизированный текст")


class EntitiesWithActionsResponse(BaseModel):
    """Найденные сущности и доступные дальнейшие действия."""

    entities: list[Entity] = Field(
        default_factory=list,
        description="Найденные сущности",
    )
    actions: list[ActionInfo] = Field(
        default_factory=list,
        description="Рекомендуемые действия, которые можно выполнить дальше",
    )
