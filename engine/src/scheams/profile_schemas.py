from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProfileDefinition(BaseModel):
    """Нормализованная конфигурация профиля (то, что реально используется в `/base`)."""

    extractors: list[str] = Field(
        min_length=1,
        description="Список детекторов (экстракторов) по их имени из `/v1/meta/detectors`",
        examples=[["passport", "inn", "phone"], ["email"]],
    )
    placeholder: str = Field(
        default="[СКРЫТО]",
        description="Строка-замена, используемая в анонимизации",
        examples=["[СКРЫТО]", "[HIDDEN]", "<redacted>"],
    )
    remove_overlaps: bool = Field(
        default=True,
        description="Удалять пересекающиеся сущности (оставлять более уверенные)",
        examples=[True],
    )


class ProfileResponse(BaseModel):
    """Профиль, сохранённый в хранилище."""

    id: str
    name: str = Field(description="Имя профиля (человекочитаемое)")
    description: str | None = Field(
        default=None,
        description="Описание профиля (для UI/админ-панели)",
        examples=["Базовый профиль для документов", "Только email адреса"],
    )
    definition: ProfileDefinition
    yaml: str = Field(description="Исходный YAML (как был загружен по API)")
    is_active: bool = Field(description="Активен ли профиль сейчас")
    is_deleted: bool = Field(description="Помечен ли профиль удалённым (soft-delete)")
    created_at: datetime = Field(description="Время создания (UTC)")
    updated_at: datetime = Field(description="Время последнего изменения (UTC)")


class ProfilesListResponse(BaseModel):
    profiles: list[ProfileResponse] = Field(
        default_factory=list, description="Список профилей"
    )


class ActiveProfileResponse(BaseModel):
    active: ProfileResponse | None = Field(
        default=None, description="Активный профиль или null"
    )


class ProfileCreateJsonRequest(BaseModel):
    """Создание профиля через JSON (без загрузки YAML файла)."""

    name: str = Field(
        description="Имя профиля",
        examples=["default", "email_only", "natasha_mix"],
    )
    description: str | None = Field(
        default=None,
        description="Описание профиля (для UI/админ-панели)",
        examples=["По умолчанию для /base", "Профиль для поиска email"],
    )
    definition: ProfileDefinition = Field(
        description="Конфигурация профиля",
        examples=[
            {"extractors": ["passport", "inn", "phone"], "placeholder": "[СКРЫТО]", "remove_overlaps": True},
            {"extractors": ["email"], "placeholder": "[HIDDEN]", "remove_overlaps": True},
        ],
    )
    activate: bool = Field(
        default=False,
        description="Сделать профиль активным (деактивирует предыдущий)",
    )
