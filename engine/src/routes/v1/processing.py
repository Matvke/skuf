from extractors import ExtractionPipeline
from extractors.models import Entity
from fastapi import APIRouter
from scheams.processing_schemas import ProcessingBody

processing_router = APIRouter(prefix="/processing")


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
    description="Возвращает выявленные сущности по экстракторам 'passport', 'inn', 'phone'",
    tags=[
        "processing",
    ],
)
async def processing_base(body: ProcessingBody):
    pipeline = ExtractionPipeline.from_registry("passport", "inn", "phone")
    result = [pipeline.run(body.text)]
    return result
