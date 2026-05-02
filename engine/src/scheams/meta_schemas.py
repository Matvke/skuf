from __future__ import annotations

from pydantic import BaseModel, Field


class DetectorInfo(BaseModel):
    """Описание доступного детектора (экстрактора)."""

    name: str = Field(description="Короткое имя детектора (используется в профилях)")
    entity_types: list[str] = Field(
        default_factory=list,
        description="Типы сущностей, которые может возвращать детектор",
    )


class DetectorsResponse(BaseModel):
    detectors: list[DetectorInfo] = Field(
        default_factory=list,
        description="Список доступных детекторов (экстракторов)",
    )


class ActionInfo(BaseModel):
    """Описание поддерживаемого действия API (высокоуровневой операции)."""

    id: str = Field(description="Уникальный идентификатор действия")
    method: str = Field(description="HTTP метод")
    path: str = Field(description="Путь эндпоинта (без host)")
    summary: str = Field(description="Короткое описание")


class ActionsResponse(BaseModel):
    actions: list[ActionInfo] = Field(
        default_factory=list,
        description="Список доступных действий",
    )

