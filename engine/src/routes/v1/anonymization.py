from extractors import ExtractionPipeline
from fastapi import APIRouter
from scheams.processing_schemas import ProcessingBody

anonimization_router = APIRouter(prefix="/anonimization")


@anonimization_router.post("/all")
async def processing_all(body: ProcessingBody):
    pipeline = ExtractionPipeline.from_registry()
    result = [pipeline.anonymize(body.text)]
    return result


@anonimization_router.post("/base")
async def processing_base(body: ProcessingBody):
    pipeline = ExtractionPipeline.from_registry("passport", "inn", "phone")
    result = [pipeline.anonymize(body.text)]
    return result
