from fastapi import APIRouter
from scheams.processing import ProcessingBody

processing_router = APIRouter(prefix="/processing")


@processing_router.post("/")
async def processing(body: ProcessingBody):
    body.text = "Anonymous text"
    return body
