from extractors import ExtractionPipeline
from fastapi import APIRouter, Depends
from profiles.deps import get_profile_store
from profiles.store import ProfileStore
from scheams.processing_schemas import (
    EntitiesResponse,
    ProcessingBody,
)

processing_router = APIRouter(prefix="/processing", tags=["processing"])

DEFAULT_BASE_EXTRACTORS = ("passport", "inn", "phone")


@processing_router.post(
    "/all",
    summary="Детекция по всем детекторам",
    description="Запускает все доступные детекторы и возвращает найденные сущности.",
    response_model=EntitiesResponse,
    response_description="Список сущностей",
)
async def processing_all(body: ProcessingBody) -> EntitiesResponse:
    pipeline = ExtractionPipeline.from_registry()
    entities = pipeline.run(body.text)
    return EntitiesResponse(entities=entities)


@processing_router.post(
    "/base",
    summary="Детекция по активному профилю",
    description=(
        "Использует активный профиль из хранилища (в момент времени активен только один). "
        "Если активного профиля нет, используется дефолтный набор: passport, inn, phone."
    ),
    response_model=EntitiesResponse,
    response_description="Список сущностей",
)
async def processing_base(
    body: ProcessingBody,
    store: ProfileStore = Depends(get_profile_store),
):
    active = await store.get_active()
    extractors = (
        active.definition.extractors
        if active is not None
        else list(DEFAULT_BASE_EXTRACTORS)
    )
    remove_overlaps = active.definition.remove_overlaps if active is not None else True
    pipeline = ExtractionPipeline.from_registry(*extractors)
    entities = pipeline.run(body.text, remove_overlaps=remove_overlaps)
    return EntitiesResponse(entities=entities)
