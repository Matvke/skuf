from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from profiles.deps import get_profile_store
from profiles.store import ProfileStore, ProfileYamlError

profiles_router = APIRouter(prefix="/profiles", tags=["profiles"])


@profiles_router.get(
    "",
    description="Список профилей (по умолчанию без удалённых)",
)
async def list_profiles(
    include_deleted: bool = False,
    store: ProfileStore = Depends(get_profile_store),
):
    profiles = await store.list_profiles(include_deleted=include_deleted)
    return [p.to_dict() for p in profiles]


@profiles_router.get(
    "/active",
    description="Текущий активный профиль",
)
async def get_active_profile(store: ProfileStore = Depends(get_profile_store)):
    profile = await store.get_active()
    if profile is None:
        return {"active": None}
    return {"active": profile.to_dict()}


@profiles_router.get(
    "/{profile_id}",
    description="Профиль по id",
)
async def get_profile(profile_id: str, store: ProfileStore = Depends(get_profile_store)):
    profile = await store.get(profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return profile.to_dict()


@profiles_router.post(
    "",
    description="Создать профиль из YAML файла (multipart/form-data)",
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    activate: bool = Form(default=False),
    store: ProfileStore = Depends(get_profile_store),
):
    yaml_text = (await file.read()).decode("utf-8", errors="replace")
    name_hint = (file.filename or "").rsplit(".", 1)[0] or None
    try:
        profile = await store.create_from_yaml(
            yaml_text, activate=activate, name_hint=name_hint, name_override=name
        )
    except ProfileYamlError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return profile.to_dict()


@profiles_router.put(
    "/{profile_id}",
    description="Обновить профиль (заменить YAML). Удалённые профили обновлять нельзя.",
)
async def update_profile(
    profile_id: str,
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    activate: bool = Form(default=False),
    store: ProfileStore = Depends(get_profile_store),
):
    yaml_text = (await file.read()).decode("utf-8", errors="replace")
    name_hint = (file.filename or "").rsplit(".", 1)[0] or None
    try:
        profile = await store.update_from_yaml(
            profile_id, yaml_text, activate=activate, name_hint=name_hint, name_override=name
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found") from exc
    except ProfileYamlError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return profile.to_dict()


@profiles_router.post(
    "/{profile_id}/activate",
    description="Сделать профиль активным (в момент времени активен только один)",
)
async def activate_profile(
    profile_id: str, store: ProfileStore = Depends(get_profile_store)
):
    try:
        profile = await store.activate(profile_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return profile.to_dict()


@profiles_router.delete(
    "/{profile_id}",
    description="Удалить профиль (мягко): помечается удалённым, но не удаляется физически",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_profile(profile_id: str, store: ProfileStore = Depends(get_profile_store)):
    try:
        await store.delete(profile_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found") from exc
    return None

