import re
from typing import Iterator

from ..base import BaseExtractor
from ..models import Entity, RegexPattern, Span


class BaseRegexExtractor(BaseExtractor):
    """
    Базовый класс для regex-экстракторов.

    Подкласс должен определить:
        - name: str
        - entity_types: tuple[str, ...]
        - patterns: list[RegexPattern]
    """

    patterns: list[RegexPattern] = []

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls._compiled = [p.compile() for p in cls.patterns]

    def extract(self, text: str) -> Iterator[Entity]:
        for regex in self._compiled:
            for match in regex.finditer(text):
                if not self.validate(match):
                    continue

                raw = match.group(0)
                yield Entity(
                    entity_type=self.entity_types[0],
                    text=raw,
                    span=Span(match.start(), match.end()),
                    normal_form=self.normalize(match),
                    details=self.build_details(match),
                    confidence=self.confidence(match),
                    source=self.name,
                )

    def validate(self, match):
        return True

    def normalize(self, match):
        return re.sub(r"\s+", " ", match.group(0)).strip()

    def build_details(self, match):
        return {k: v for k, v in match.groupdict().items() if v is not None}

    def confidence(self, match: re.Match) -> float:
        return 1.0
