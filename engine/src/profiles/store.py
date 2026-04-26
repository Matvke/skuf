from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError
from sqlalchemy import Boolean, DateTime, Index, String, Text, desc, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from extractors import registry
from scheams.profile_schemas import ProfileDefinition


class ProfileYamlError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProfileRecord:
    id: str
    name: str
    definition: ProfileDefinition
    yaml: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "definition": self.definition.model_dump(),
            "yaml": self.yaml,
            "is_active": self.is_active,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def parse_profile_yaml(
    yaml_text: str,
    *,
    name_hint: str | None = None,
) -> tuple[str, ProfileDefinition]:
    try:
        raw = yaml.safe_load(yaml_text)
    except Exception as exc:  # noqa: BLE001
        raise ProfileYamlError(f"Invalid YAML: {exc}") from exc

    if not isinstance(raw, dict):
        raise ProfileYamlError("YAML должен содержать mapping (словарь) верхнего уровня")

    name = raw.get("name") or name_hint
    if not name or not isinstance(name, str):
        raise ProfileYamlError("Не удалось определить имя профиля (поле `name` или имя файла)")

    extractors = raw.get("extractors") or raw.get("base_extractors")
    if extractors is None:
        raise ProfileYamlError("В YAML обязателен ключ `extractors` (list[str])")

    definition_payload: dict[str, Any] = {
        "extractors": extractors,
        "placeholder": raw.get("placeholder", "[СКРЫТО]"),
        "remove_overlaps": raw.get("remove_overlaps", True),
    }

    try:
        definition = ProfileDefinition.model_validate(definition_payload)
    except ValidationError as exc:
        raise ProfileYamlError(str(exc)) from exc

    deduped = _dedupe_preserve_order(definition.extractors)
    definition = definition.model_copy(update={"extractors": deduped})

    available = set(registry.all_names())
    unknown = [
        extractor_name
        for extractor_name in definition.extractors
        if extractor_name not in available
    ]
    if unknown:
        raise ProfileYamlError(
            f"Неизвестные экстракторы: {unknown}. Доступные: {sorted(available)}"
        )

    return name, definition


class Base(DeclarativeBase):
    pass


class ProfileRow(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    yaml: Mapped[str] = mapped_column(Text, nullable=False)
    definition_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


Index("idx_profiles_updated_at", ProfileRow.updated_at.desc())
Index("idx_profiles_active", ProfileRow.is_active)
Index("idx_profiles_deleted", ProfileRow.is_deleted)
Index(
    "idx_only_one_active_profile",
    ProfileRow.is_active,
    unique=True,
    sqlite_where=(ProfileRow.is_active.is_(True) & ProfileRow.is_deleted.is_(False)),
)


def _row_to_record(row: ProfileRow) -> ProfileRecord:
    definition = ProfileDefinition.model_validate(json.loads(row.definition_json))
    return ProfileRecord(
        id=row.id,
        name=row.name,
        definition=definition,
        yaml=row.yaml,
        is_active=bool(row.is_active),
        is_deleted=bool(row.is_deleted),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class ProfileStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        storage_dir = Path(os.getenv("ENGINE_STORAGE_DIR", "data"))
        default_db = storage_dir / "profiles.sqlite3"
        self._db_path = Path(db_path) if db_path is not None else default_db
        self._init_lock = asyncio.Lock()
        self._initialized = False
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None

    @property
    def db_path(self) -> Path:
        return self._db_path

    @property
    def _db_url(self) -> str:
        return f"sqlite+aiosqlite:///{self._db_path.as_posix()}"

    async def init(self) -> None:
        async with self._init_lock:
            if self._initialized:
                return

            self._db_path.parent.mkdir(parents=True, exist_ok=True)

            self._engine = create_async_engine(self._db_url, future=True)
            self._sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False)

            async with self._engine.begin() as conn:
                await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
                await conn.run_sync(Base.metadata.create_all)

            self._initialized = True

    async def close(self) -> None:
        if self._engine is None:
            return
        await self._engine.dispose()

    async def ensure_seed_profile(self) -> None:
        await self.init()
        active = await self.get_active()
        if active is not None:
            return
        profiles = await self.list_profiles(include_deleted=True)
        if profiles:
            return

        seed_yaml = yaml.safe_dump(
            {
                "name": "default",
                "extractors": ["passport", "inn", "phone"],
                "placeholder": "[СКРЫТО]",
                "remove_overlaps": True,
            },
            sort_keys=False,
            allow_unicode=True,
        )
        await self.create_from_yaml(seed_yaml, activate=True, name_hint="default")

    def _require_sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        if self._sessionmaker is None:
            raise RuntimeError("ProfileStore is not initialized")
        return self._sessionmaker

    def _new_session(self) -> AsyncSession:
        return self._require_sessionmaker()()

    async def list_profiles(self, *, include_deleted: bool = False) -> list[ProfileRecord]:
        await self.init()
        async with self._new_session() as session:
            stmt = select(ProfileRow).order_by(desc(ProfileRow.updated_at))
            if not include_deleted:
                stmt = stmt.where(ProfileRow.is_deleted.is_(False))
            rows = (await session.scalars(stmt)).all()
        return [_row_to_record(r) for r in rows]

    async def get(self, profile_id: str) -> ProfileRecord | None:
        await self.init()
        async with self._new_session() as session:
            row = await session.get(ProfileRow, profile_id)
        return _row_to_record(row) if row is not None else None

    async def get_active(self) -> ProfileRecord | None:
        await self.init()
        async with self._new_session() as session:
            stmt = (
                select(ProfileRow)
                .where(ProfileRow.is_active.is_(True), ProfileRow.is_deleted.is_(False))
                .limit(1)
            )
            row = await session.scalar(stmt)
        return _row_to_record(row) if row is not None else None

    async def create_from_yaml(
        self,
        yaml_text: str,
        *,
        activate: bool = False,
        name_hint: str | None = None,
        name_override: str | None = None,
    ) -> ProfileRecord:
        await self.init()
        name, definition = parse_profile_yaml(yaml_text, name_hint=name_hint)
        if name_override:
            name = name_override

        if not activate and await self.get_active() is None:
            activate = True

        profile_id = uuid.uuid4().hex
        now = _utc_now()
        definition_json = json.dumps(definition.model_dump(), ensure_ascii=False)

        async with self._new_session() as session:
            async with session.begin():
                if activate:
                    await session.execute(
                        update(ProfileRow)
                        .where(ProfileRow.is_active.is_(True))
                        .values(is_active=False)
                    )

                session.add(
                    ProfileRow(
                        id=profile_id,
                        name=name,
                        yaml=yaml_text,
                        definition_json=definition_json,
                        created_at=now,
                        updated_at=now,
                        is_active=activate,
                        is_deleted=False,
                    )
                )

            row = await session.get(ProfileRow, profile_id)
            if row is None:
                raise RuntimeError("Failed to create profile")
            return _row_to_record(row)

    async def update_from_yaml(
        self,
        profile_id: str,
        yaml_text: str,
        *,
        activate: bool = False,
        name_hint: str | None = None,
        name_override: str | None = None,
    ) -> ProfileRecord:
        await self.init()
        current = await self.get(profile_id)
        if current is None:
            raise KeyError(profile_id)
        if current.is_deleted:
            raise ValueError("Profile is deleted")

        name, definition = parse_profile_yaml(yaml_text, name_hint=name_hint or current.name)
        if name_override:
            name = name_override

        now = _utc_now()
        definition_json = json.dumps(definition.model_dump(), ensure_ascii=False)

        try:
            async with self._new_session() as session:
                async with session.begin():
                    if activate:
                        await session.execute(
                            update(ProfileRow)
                            .where(ProfileRow.is_active.is_(True))
                            .values(is_active=False)
                        )

                    await session.execute(
                        update(ProfileRow)
                        .where(ProfileRow.id == profile_id, ProfileRow.is_deleted.is_(False))
                        .values(
                            name=name,
                            yaml=yaml_text,
                            definition_json=definition_json,
                            updated_at=now,
                            is_active=(activate or current.is_active),
                        )
                    )

                row = await session.get(ProfileRow, profile_id)
                if row is None:
                    raise RuntimeError("Failed to update profile")
                return _row_to_record(row)
        except IntegrityError as exc:
            raise ValueError("Activation conflict") from exc

    async def activate(self, profile_id: str) -> ProfileRecord:
        await self.init()
        record = await self.get(profile_id)
        if record is None:
            raise KeyError(profile_id)
        if record.is_deleted:
            raise ValueError("Profile is deleted")

        now = _utc_now()
        try:
            async with self._new_session() as session:
                async with session.begin():
                    await session.execute(
                        update(ProfileRow)
                        .where(ProfileRow.is_active.is_(True))
                        .values(is_active=False)
                    )
                    result = await session.execute(
                        update(ProfileRow)
                        .where(ProfileRow.id == profile_id, ProfileRow.is_deleted.is_(False))
                        .values(is_active=True, updated_at=now)
                    )
                    if result.rowcount == 0:
                        raise KeyError(profile_id)

                row = await session.get(ProfileRow, profile_id)
                if row is None:
                    raise RuntimeError("Failed to activate profile")
                return _row_to_record(row)
        except IntegrityError as exc:
            raise ValueError("Activation conflict") from exc

    async def delete(self, profile_id: str) -> None:
        await self.init()
        record = await self.get(profile_id)
        if record is None:
            raise KeyError(profile_id)
        if record.is_deleted:
            return

        now = _utc_now()
        async with self._new_session() as session:
            async with session.begin():
                await session.execute(
                    update(ProfileRow)
                    .where(ProfileRow.id == profile_id)
                    .values(is_deleted=True, is_active=False, updated_at=now)
                )

        if record.is_active:
            candidates = await self.list_profiles(include_deleted=False)
            if candidates:
                await self.activate(candidates[0].id)
