from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProfileDefinition(BaseModel):
    extractors: list[str] = Field(min_length=1)
    placeholder: str = "[СКРЫТО]"
    remove_overlaps: bool = True


class ProfileResponse(BaseModel):
    id: str
    name: str
    definition: ProfileDefinition
    yaml: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

