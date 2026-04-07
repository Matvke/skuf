from typing import Iterator

from ..base import BaseExtractor
from ..models import Entity, Span
from ..registry import registry
from .base_natasha import BaseNatashaExtractor


@registry.register
class PersonExtractor(BaseNatashaExtractor, BaseExtractor):
    name = "person"
    entity_types = ("PERSON",)

    def extract(self, text: str) -> Iterator[Entity]:
        doc = self._natasha.make_doc(text)

        name_details: dict[tuple, dict] = {}
        for match in self._natasha.names_extractor(text):
            fact = match.fact
            name_details[(match.start, match.stop)] = {
                k: v
                for k, v in {
                    "first": fact.first,
                    "last": fact.last,
                    "middle": fact.middle,
                }.items()
                if v
            }

        for span in doc.spans:
            if span.type != "PER":
                continue
            details = name_details.get((span.start, span.stop), {})
            yield Entity(
                entity_type="PERSON",
                text=text[span.start : span.stop],
                span=Span(span.start, span.stop),
                normal_form=span.normal,
                details=details,
                source=self.name,
            )
