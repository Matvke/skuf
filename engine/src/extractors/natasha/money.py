from typing import Iterator

from ..base import BaseExtractor
from ..models import Entity, Span
from ..registry import registry
from .base_natasha import BaseNatashaExtractor


@registry.register
class MoneyExtractor(BaseNatashaExtractor, BaseExtractor):
    name = "money"
    entity_types = ("MONEY",)

    def extract(self, text: str) -> Iterator[Entity]:
        for match in self._natasha.money_extractor(text):
            fact = match.fact
            details = {
                k: v
                for k, v in {
                    "amount": fact.amount,
                    "currency": fact.currency,
                }.items()
                if v
            }

            parts = [str(details[k]) for k in ("amount", "currency") if k in details]

            yield Entity(
                entity_type="MONEY",
                text=text[match.start : match.stop],
                span=Span(match.start, match.stop),
                normal_form=" ".join(parts) or None,
                details=details,
                source=self.name,
            )
