from __future__ import annotations

from fastapi import FastAPI

from profiles import ProfileStore
from routes import v1_router
from scheams.common_schemas import HealthResponse

def create_app(*, profiles_db_path: str | None = None) -> FastAPI:
    app = FastAPI(
        title="Anonymization Engine API",
        version="0.1.0",
        description=(
            "Сервис для детекции и анонимизации чувствительных данных. "
            "Поддерживает профили (YAML), загружаемые из админ-панели, "
            "и быстрое переключение активного профиля."
        ),
        openapi_tags=[
            {"name": "meta", "description": "Метаданные: детекторы и действия API"},
            {"name": "profiles", "description": "CRUD профилей (YAML) и активация"},
            {"name": "processing", "description": "Детекция сущностей в тексте"},
            {"name": "anonimization", "description": "Анонимизация текста"},
        ],
    )

    app.include_router(v1_router)
    app.state.profile_store = ProfileStore(db_path=profiles_db_path)

    @app.on_event("startup")
    async def _startup() -> None:
        await app.state.profile_store.ensure_seed_profile()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await app.state.profile_store.close()

    @app.get(
        "/",
        summary="Healthcheck",
        description="Простой healthcheck эндпоинт.",
        response_model=HealthResponse,
    )
    async def home() -> HealthResponse:
        return HealthResponse(healthy=True)

    return app


app = create_app()
