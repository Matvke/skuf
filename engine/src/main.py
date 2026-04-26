from __future__ import annotations

from fastapi import FastAPI

from profiles import ProfileStore
from routes import v1_router

def create_app(*, profiles_db_path: str | None = None) -> FastAPI:
    app = FastAPI(
        title="Anonymization Engine API",
        version="0.1.0",
    )

    app.include_router(v1_router)
    app.state.profile_store = ProfileStore(db_path=profiles_db_path)

    @app.on_event("startup")
    async def _startup() -> None:
        await app.state.profile_store.ensure_seed_profile()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await app.state.profile_store.close()

    @app.get("/")
    async def home():
        return {"healthy": "true"}

    return app


app = create_app()
