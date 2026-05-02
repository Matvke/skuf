from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from profiles.deps import get_profile_store
from profiles.store import ProfileStore, ProfileYamlError
from scheams.profile_schemas import (
    ActiveProfileResponse,
    ProfileCreateJsonRequest,
    ProfileResponse,
    ProfilesListResponse,
)

profiles_router = APIRouter(prefix="/profiles", tags=["profiles"])


@profiles_router.get(
    "",
    summary="Список профилей",
    description="Возвращает список профилей из хранилища. По умолчанию удалённые (soft-delete) не показываются.",
    response_model=ProfilesListResponse,
)
async def list_profiles(
    include_deleted: bool = Query(
        default=False, description="Включать ли профили, помеченные удалёнными"
    ),
    store: ProfileStore = Depends(get_profile_store),
):
    profiles = await store.list_profiles(include_deleted=include_deleted)
    return ProfilesListResponse(
        profiles=[ProfileResponse.model_validate(p.to_dict()) for p in profiles]
    )


@profiles_router.get(
    "/active",
    summary="Активный профиль",
    description="Возвращает активный профиль или null, если активного профиля нет.",
    response_model=ActiveProfileResponse,
)
async def get_active_profile(store: ProfileStore = Depends(get_profile_store)):
    profile = await store.get_active()
    if profile is None:
        return ActiveProfileResponse(active=None)
    return ActiveProfileResponse(active=ProfileResponse.model_validate(profile.to_dict()))


@profiles_router.get(
    "/{profile_id}",
    summary="Профиль по id",
    description="Возвращает профиль по его id (включая YAML, по которому он был загружен).",
    response_model=ProfileResponse,
)
async def get_profile(profile_id: str, store: ProfileStore = Depends(get_profile_store)):
    profile = await store.get(profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return ProfileResponse.model_validate(profile.to_dict())


@profiles_router.post(
    "",
    summary="Создать профиль",
    description=(
        "Создаёт профиль из YAML файла. "
        "Файл передаётся как `multipart/form-data` поле `file`. "
        "Если `activate=true`, профиль становится активным (и деактивирует предыдущий)."
    ),
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    file: UploadFile = File(..., description="YAML файл профиля"),
    name: str | None = Form(default=None, description="Переопределить имя профиля"),
    description: str | None = Form(
        default=None, description="Переопределить описание профиля"
    ),
    activate: bool = Form(default=False, description="Сделать профиль активным"),
    store: ProfileStore = Depends(get_profile_store),
):
    yaml_text = (await file.read()).decode("utf-8", errors="replace")
    name_hint = (file.filename or "").rsplit(".", 1)[0] or None
    try:
        profile = await store.create_from_yaml(
            yaml_text,
            activate=activate,
            name_hint=name_hint,
            name_override=name,
            description_override=description,
        )
    except ProfileYamlError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ProfileResponse.model_validate(profile.to_dict())


@profiles_router.post(
    "/json",
    summary="Создать профиль (JSON)",
    description=(
        "Создаёт профиль из JSON тела запроса. "
        "Профиль всё равно сохраняется как YAML (генерируется автоматически) для единообразия хранения."
    ),
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile_json(
    body: ProfileCreateJsonRequest,
    store: ProfileStore = Depends(get_profile_store),
) -> ProfileResponse:
    try:
        profile = await store.create_from_definition(
            name=body.name,
            description=body.description,
            definition=body.definition,
            activate=body.activate,
        )
    except ProfileYamlError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ProfileResponse.model_validate(profile.to_dict())


@profiles_router.put(
    "/{profile_id}",
    summary="Обновить профиль",
    description=(
        "Полностью заменяет YAML профиля. "
        "Удалённые (soft-delete) профили обновлять нельзя."
    ),
    response_model=ProfileResponse,
)
async def update_profile(
    profile_id: str,
    file: UploadFile = File(..., description="Новый YAML файл профиля"),
    name: str | None = Form(default=None, description="Переопределить имя профиля"),
    description: str | None = Form(
        default=None, description="Переопределить описание профиля"
    ),
    activate: bool = Form(default=False, description="Сделать профиль активным"),
    store: ProfileStore = Depends(get_profile_store),
):
    yaml_text = (await file.read()).decode("utf-8", errors="replace")
    name_hint = (file.filename or "").rsplit(".", 1)[0] or None
    try:
        profile = await store.update_from_yaml(
            profile_id,
            yaml_text,
            activate=activate,
            name_hint=name_hint,
            name_override=name,
            description_override=description,
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found") from exc
    except ProfileYamlError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ProfileResponse.model_validate(profile.to_dict())


@profiles_router.post(
    "/{profile_id}/activate",
    summary="Активировать профиль",
    description="Делает профиль активным. В конкретный момент времени активен только один профиль.",
    response_model=ProfileResponse,
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
    return ProfileResponse.model_validate(profile.to_dict())


@profiles_router.delete(
    "/{profile_id}",
    summary="Удалить профиль (soft-delete)",
    description="Помечает профиль удалённым и деактивирует его. Профиль физически не удаляется.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_profile(profile_id: str, store: ProfileStore = Depends(get_profile_store)):
    try:
        await store.delete(profile_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found") from exc
    return None
