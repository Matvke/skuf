from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    healthy: bool = Field(description="Состояние сервиса")

