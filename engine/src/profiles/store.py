from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite
import yaml
from pydantic import ValidationError

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


class ProfileStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        storage_dir = Path(os.getenv("ENGINE_STORAGE_DIR", "data"))
        default_db = storage_dir / "profiles.sqlite3"
        self._db_path = Path(db_path) if db_path is not None else default_db
        self._init_lock = asyncio.Lock()
        self._initialized = False

    @property
    def db_path(self) -> Path:
        return self._db_path

    async def init(self) -> None:
        async with self._init_lock:
            if self._initialized:
                return

            self._db_path.parent.mkdir(parents=True, exist_ok=True)

            async with self._db() as db:
                await db.execute("PRAGMA journal_mode=WAL;")
                await db.execute("PRAGMA foreign_keys=ON;")
                await db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS profiles (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        yaml TEXT NOT NULL,
                        definition_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_active INTEGER NOT NULL DEFAULT 0,
                        is_deleted INTEGER NOT NULL DEFAULT 0
                    );

                    CREATE INDEX IF NOT EXISTS idx_profiles_updated_at
                    ON profiles(updated_at DESC);

                    CREATE INDEX IF NOT EXISTS idx_profiles_active
                    ON profiles(is_active);

                    CREATE INDEX IF NOT EXISTS idx_profiles_deleted
                    ON profiles(is_deleted);

                    CREATE UNIQUE INDEX IF NOT EXISTS idx_only_one_active_profile
                    ON profiles(is_active)
                    WHERE is_active = 1 AND is_deleted = 0;
                    """
                )
                await db.commit()

            self._initialized = True

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

    @asynccontextmanager
    async def _db(self):
        async with aiosqlite.connect(self._db_path.as_posix()) as db:
            db.row_factory = aiosqlite.Row
            yield db

    @staticmethod
    def _row_to_record(row: aiosqlite.Row) -> ProfileRecord:
        definition = ProfileDefinition.model_validate(json.loads(row["definition_json"]))
        return ProfileRecord(
            id=row["id"],
            name=row["name"],
            definition=definition,
            yaml=row["yaml"],
            is_active=bool(row["is_active"]),
            is_deleted=bool(row["is_deleted"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    async def list_profiles(self, *, include_deleted: bool = False) -> list[ProfileRecord]:
        await self.init()
        where = "" if include_deleted else "WHERE is_deleted = 0"
        async with self._db() as db:
            cur = await db.execute(
                f"""
                SELECT * FROM profiles
                {where}
                ORDER BY updated_at DESC
                """
            )
            rows = await cur.fetchall()
        return [self._row_to_record(r) for r in rows]

    async def get(self, profile_id: str) -> ProfileRecord | None:
        await self.init()
        async with self._db() as db:
            cur = await db.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
            row = await cur.fetchone()
        return self._row_to_record(row) if row is not None else None

    async def get_active(self) -> ProfileRecord | None:
        await self.init()
        async with self._db() as db:
            cur = await db.execute(
                "SELECT * FROM profiles WHERE is_active = 1 AND is_deleted = 0 LIMIT 1"
            )
            row = await cur.fetchone()
        return self._row_to_record(row) if row is not None else None

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
        now = _utc_now().isoformat()
        definition_json = json.dumps(definition.model_dump(), ensure_ascii=False)

        async with self._db() as db:
            await db.execute("BEGIN IMMEDIATE")
            if activate:
                await db.execute(
                    "UPDATE profiles SET is_active = 0 WHERE is_active = 1"
                )
            await db.execute(
                """
                INSERT INTO profiles (
                    id, name, yaml, definition_json,
                    created_at, updated_at, is_active, is_deleted
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (profile_id, name, yaml_text, definition_json, now, now, int(activate)),
            )
            await db.commit()

        record = await self.get(profile_id)
        if record is None:
            raise RuntimeError("Failed to create profile")
        return record

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

        now = _utc_now().isoformat()
        definition_json = json.dumps(definition.model_dump(), ensure_ascii=False)

        async with self._db() as db:
            await db.execute("BEGIN IMMEDIATE")
            if activate:
                await db.execute("UPDATE profiles SET is_active = 0 WHERE is_active = 1")
            await db.execute(
                """
                UPDATE profiles
                SET name = ?, yaml = ?, definition_json = ?, updated_at = ?, is_active = ?
                WHERE id = ? AND is_deleted = 0
                """,
                (name, yaml_text, definition_json, now, int(activate or current.is_active), profile_id),
            )
            await db.commit()

        updated = await self.get(profile_id)
        if updated is None:
            raise RuntimeError("Failed to update profile")
        return updated

    async def activate(self, profile_id: str) -> ProfileRecord:
        await self.init()
        record = await self.get(profile_id)
        if record is None:
            raise KeyError(profile_id)
        if record.is_deleted:
            raise ValueError("Profile is deleted")

        async with self._db() as db:
            await db.execute("BEGIN IMMEDIATE")
            await db.execute("UPDATE profiles SET is_active = 0 WHERE is_active = 1")
            await db.execute(
                "UPDATE profiles SET is_active = 1, updated_at = ? WHERE id = ?",
                (_utc_now().isoformat(), profile_id),
            )
            await db.commit()

        active = await self.get(profile_id)
        if active is None:
            raise RuntimeError("Failed to activate profile")
        return active

    async def delete(self, profile_id: str) -> None:
        await self.init()
        record = await self.get(profile_id)
        if record is None:
            raise KeyError(profile_id)
        if record.is_deleted:
            return

        async with self._db() as db:
            await db.execute("BEGIN IMMEDIATE")
            await db.execute(
                "UPDATE profiles SET is_deleted = 1, is_active = 0, updated_at = ? WHERE id = ?",
                (_utc_now().isoformat(), profile_id),
            )
            await db.commit()

        if record.is_active:
            candidates = await self.list_profiles(include_deleted=False)
            if candidates:
                await self.activate(candidates[0].id)
