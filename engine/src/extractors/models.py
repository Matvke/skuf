from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


@dataclass
class Span:
    start: int
    stop: int

    def __len__(self):
        return self.stop - self.start

    def overlaps(self, other: Span):
        return self.start < other.stop and other.start < self.stop


class Entity(BaseModel):
    entity_type: str
    text: str
    span: Span
    normal_form: str | None = None
    confidence: float = 1.0
    details: dict[str, Any] = Field(default_factory=dict)
    source: str = ""


class RegexPattern(BaseModel):
    """Один паттерн с метаданными."""

    pattern: str
    flags: re.RegexFlag = re.IGNORECASE
    description: str = ""

    def compile(self) -> re.Pattern:
        return re.compile(self.pattern, self.flags)
