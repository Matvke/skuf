from fastapi import APIRouter

from .v1.anonymization import anonimization_router
from .v1.profiles import profiles_router
from .v1.processing import processing_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(processing_router)
v1_router.include_router(anonimization_router)
v1_router.include_router(profiles_router)
