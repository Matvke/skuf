from extractors.entity_extractor import EntityExtractor
from fastapi import APIRouter
from scheams.processing_schemas import ProcessingBody

processing_router = APIRouter(prefix="/processing")


@processing_router.post("/entity")
async def processing_entities(body: ProcessingBody):
    processor = EntityExtractor()
    return processor.anonymize(body.text)
