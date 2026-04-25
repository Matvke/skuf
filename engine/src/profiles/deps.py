from __future__ import annotations

from fastapi import Request

from .store import ProfileStore


def get_profile_store(request: Request) -> ProfileStore:
    store = getattr(request.app.state, "profile_store", None)
    if store is None:
        raise RuntimeError("ProfileStore is not initialized (app.state.profile_store)")
    return store

