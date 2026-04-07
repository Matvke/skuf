from typing import Iterator

from ..base import BaseExtractor
from ..models import Entity, Span
from ..registry import registry
from .base_natasha import BaseNatashaExtractor


@registry.register
class DateExtractor(BaseNatashaExtractor, BaseExtractor):
    name = "date"
    entity_types = ("DATE",)

    def extract(self, text: str) -> Iterator[Entity]:
        for match in self._natasha.dates_extractor(text):
            fact = match.fact
            details = {
                k: v
                for k, v in {
                    "year": fact.year,
                    "month": fact.month,
                    "day": fact.day,
                }.items()
                if v
            }

            parts = [str(details[k]) for k in ("day", "month", "year") if k in details]
            normal = ".".join(parts) or None

            yield Entity(
                entity_type="DATE",
                text=text[match.start : match.stop],
                span=Span(match.start, match.stop),
                normal_form=normal,
                details=details,
                source=self.name,
            )
