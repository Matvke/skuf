from extractors import ExtractionPipeline
from extractors.models import Entity
from fastapi import APIRouter, Depends
from profiles.deps import get_profile_store
from profiles.store import ProfileStore
from scheams.processing_schemas import ProcessingBody

processing_router = APIRouter(prefix="/processing")

DEFAULT_BASE_EXTRACTORS = ("passport", "inn", "phone")


@processing_router.post(
    "/all",
    description="Возвращает выявленные сущности по всем существующим экстракторам",
    tags=[
        "processing",
    ],
)
async def processing_all(body: ProcessingBody) -> list[list[Entity]]:
    pipeline = ExtractionPipeline.from_registry()
    result = [pipeline.run(body.text)]
    return result


@processing_router.post(
    "/base",
    description="Возвращает выявленные сущности по активному профилю (если нет профиля — 'passport', 'inn', 'phone')",
    tags=[
        "processing",
    ],
)
async def processing_base(
    body: ProcessingBody,
    store: ProfileStore = Depends(get_profile_store),
):
    active = await store.get_active()
    extractors = active.definition.extractors if active is not None else list(DEFAULT_BASE_EXTRACTORS)
    remove_overlaps = active.definition.remove_overlaps if active is not None else True
    pipeline = ExtractionPipeline.from_registry(*extractors)
    result = [pipeline.run(body.text, remove_overlaps=remove_overlaps)]
    return result
