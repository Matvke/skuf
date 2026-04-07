from extractors import ExtractionPipeline
from fastapi import APIRouter
from scheams.processing_schemas import ProcessingBody

anonimization_router = APIRouter(prefix="/anonimization")


@anonimization_router.post(
    "/all",
    description="Возвращает анонимизированный текст по всем существующим экстракторам",
    tags=["anonimization", "v1"],
)
async def processing_all(body: ProcessingBody) -> str:
    pipeline = ExtractionPipeline.from_registry()
    result = pipeline.anonymize(body.text)
    return result


@anonimization_router.post(
    "/base",
    description="Возвращает анонимизированный текст по всем экстракторам 'passport', 'inn', 'phone'",
    tags=["anonimization", "v1"],
)
async def processing_base(body: ProcessingBody) -> str:
    pipeline = ExtractionPipeline.from_registry("passport", "inn", "phone")
    result = pipeline.anonymize(body.text)
    return result
