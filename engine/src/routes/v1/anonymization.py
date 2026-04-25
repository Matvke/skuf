from extractors import ExtractionPipeline
from fastapi import APIRouter, Depends
from profiles.deps import get_profile_store
from profiles.store import ProfileStore
from scheams.processing_schemas import ProcessingBody

anonimization_router = APIRouter(prefix="/anonimization")

DEFAULT_BASE_EXTRACTORS = ("passport", "inn", "phone")


@anonimization_router.post(
    "/all",
    description="Возвращает анонимизированный текст по всем существующим экстракторам",
    tags=[
        "anonimization",
    ],
)
async def anonymize_all(body: ProcessingBody) -> str:
    pipeline = ExtractionPipeline.from_registry()
    result = pipeline.anonymize(body.text)
    return result


@anonimization_router.post(
    "/base",
    description="Возвращает анонимизированный текст по активному профилю (если нет профиля — 'passport', 'inn', 'phone')",
    tags=[
        "anonimization",
    ],
)
async def anonymize_base(
    body: ProcessingBody,
    store: ProfileStore = Depends(get_profile_store),
) -> str:
    active = await store.get_active()
    extractors = active.definition.extractors if active is not None else list(DEFAULT_BASE_EXTRACTORS)
    placeholder = active.definition.placeholder if active is not None else "[СКРЫТО]"
    remove_overlaps = active.definition.remove_overlaps if active is not None else True
    pipeline = ExtractionPipeline.from_registry(*extractors)
    result = pipeline.anonymize(
        body.text,
        placeholder=placeholder,
        remove_overlaps=remove_overlaps,
    )
    return result
