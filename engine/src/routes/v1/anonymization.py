from extractors import ExtractionPipeline
from fastapi import APIRouter, Depends
from profiles.deps import get_profile_store
from profiles.store import ProfileStore
from scheams.processing_schemas import AnonymizedTextResponse, ProcessingBody

anonimization_router = APIRouter(prefix="/anonimization", tags=["anonimization"])

DEFAULT_BASE_EXTRACTORS = ("passport", "inn", "phone")


@anonimization_router.post(
    "/all",
    summary="Анонимизация по всем детекторам",
    description="Запускает все доступные детекторы и заменяет найденные сущности на placeholder.",
    response_model=AnonymizedTextResponse,
    response_description="Анонимизированный текст",
)
async def anonymize_all(body: ProcessingBody) -> AnonymizedTextResponse:
    pipeline = ExtractionPipeline.from_registry()
    text = pipeline.anonymize(body.text)
    return AnonymizedTextResponse(text=text)


@anonimization_router.post(
    "/base",
    summary="Анонимизация по активному профилю",
    description=(
        "Использует активный профиль из хранилища (в момент времени активен только один). "
        "Если активного профиля нет, используется дефолтный набор: passport, inn, phone."
    ),
    response_model=AnonymizedTextResponse,
    response_description="Анонимизированный текст",
)
async def anonymize_base(
    body: ProcessingBody,
    store: ProfileStore = Depends(get_profile_store),
) -> AnonymizedTextResponse:
    active = await store.get_active()
    extractors = active.definition.extractors if active is not None else list(DEFAULT_BASE_EXTRACTORS)
    placeholder = active.definition.placeholder if active is not None else "[СКРЫТО]"
    remove_overlaps = active.definition.remove_overlaps if active is not None else True
    pipeline = ExtractionPipeline.from_registry(*extractors)
    text = pipeline.anonymize(
        body.text,
        placeholder=placeholder,
        remove_overlaps=remove_overlaps,
    )
    return AnonymizedTextResponse(text=text)
