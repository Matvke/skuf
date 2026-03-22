from fastapi import APIRouter

from .v1.processing import processing_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(processing_router)
