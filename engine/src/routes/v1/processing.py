from fastapi import APIRouter

from scheams.processing_schemas import ProcessingBody
from services.processing_service import NameExtractor

processing_router = APIRouter(prefix="/processing")


@processing_router.post("/")
async def processing(body: ProcessingBody):
    processor = NameExtractor()
    return processor.extract_with_positions(body.text)
