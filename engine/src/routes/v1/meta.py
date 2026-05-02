from __future__ import annotations

from fastapi import APIRouter

from extractors import registry
from scheams.meta_schemas import ActionInfo, ActionsResponse, DetectorInfo, DetectorsResponse

meta_router = APIRouter(prefix="/meta", tags=["meta"])


@meta_router.get(
    "/detectors",
    summary="Список детекторов",
    description="Возвращает все доступные детекторы (экстракторы), которые можно указывать в YAML профилях.",
    response_model=DetectorsResponse,
)
async def get_detectors() -> DetectorsResponse:
    detectors = []
    for name, cls in sorted(registry.all_extractors().items(), key=lambda x: x[0]):
        entity_types = list(getattr(cls, "entity_types", ()) or ())
        detectors.append(DetectorInfo(name=name, entity_types=entity_types))
    return DetectorsResponse(detectors=detectors)


@meta_router.get(
    "/actions",
    summary="Список действий API",
    description="Человекочитаемый список основных действий, поддерживаемых сервисом.",
    response_model=ActionsResponse,
)
async def get_actions() -> ActionsResponse:
    actions = [
        ActionInfo(
            id="processing.all",
            method="POST",
            path="/v1/processing/all",
            summary="Детекция по всем детекторам",
        ),
        ActionInfo(
            id="processing.base",
            method="POST",
            path="/v1/processing/base",
            summary="Детекция по активному профилю",
        ),
        ActionInfo(
            id="processing.actions",
            method="GET",
            path="/v1/processing/actions",
            summary="Действия для найденных сущностей",
        ),
        ActionInfo(
            id="anonymization.all",
            method="POST",
            path="/v1/anonimization/all",
            summary="Анонимизация по всем детекторам",
        ),
        ActionInfo(
            id="anonymization.base",
            method="POST",
            path="/v1/anonimization/base",
            summary="Анонимизация по активному профилю",
        ),
        ActionInfo(
            id="profiles.list",
            method="GET",
            path="/v1/profiles",
            summary="Список профилей",
        ),
        ActionInfo(
            id="profiles.create",
            method="POST",
            path="/v1/profiles",
            summary="Создать профиль (YAML файл)",
        ),
        ActionInfo(
            id="profiles.create_json",
            method="POST",
            path="/v1/profiles/json",
            summary="Создать профиль (JSON)",
        ),
        ActionInfo(
            id="profiles.active",
            method="GET",
            path="/v1/profiles/active",
            summary="Активный профиль",
        ),
    ]
    return ActionsResponse(actions=actions)
