from typing import Iterator

from ..base import BaseExtractor
from ..models import Entity, Span
from ..registry import registry
from .base_natasha import BaseNatashaExtractor


@registry.register
class LocationExtractor(BaseNatashaExtractor, BaseExtractor):
    name = "location"
    entity_types = ("LOCATION",)

    def extract(self, text: str) -> Iterator[Entity]:
        doc = self._natasha.make_doc(text)
        seen: set[tuple[int, int]] = set()

        for span in doc.spans:
            if span.type == "LOC":
                seen.add((span.start, span.stop))
                yield Entity(
                    entity_type="LOCATION",
                    text=text[span.start : span.stop],
                    span=Span(span.start, span.stop),
                    normal_form=span.normal,
                    source=self.name,
                )

        for match in self._natasha.addr_extractor(text):
            if (match.start, match.stop) in seen:
                continue
            fact = match.fact
            details = {
                attr: getattr(fact, attr)
                for attr in ("country", "region", "city", "street", "house")
                if getattr(fact, attr, None)
            }
            yield Entity(
                entity_type="LOCATION",
                text=text[match.start : match.stop],
                span=Span(match.start, match.stop),
                normal_form=", ".join(details.values()) or None,
                details=details,
                source=self.name,
            )
