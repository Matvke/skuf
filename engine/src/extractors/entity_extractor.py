from dataclasses import dataclass, field
from typing import Optional

from natasha import (
    AddrExtractor,
    DatesExtractor,
    Doc,
    MoneyExtractor,
    MorphVocab,
    NamesExtractor,
    NewsEmbedding,
    NewsMorphTagger,
    NewsNERTagger,
    NewsSyntaxParser,
    Segmenter,
)


@dataclass
class ExtractedEntity:
    entity_type: str
    text: str
    start: int
    stop: int
    normal_form: Optional[str] = None
    details: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        details_str = f", details={self.details}" if self.details else ""
        normal_str = f", normal='{self.normal_form}'" if self.normal_form else ""
        return (
            f"ExtractedEntity(type='{self.entity_type}', "
            f"text='{self.text}'{normal_str}"
            f"{details_str}, span=({self.start}, {self.stop}))"
        )


class EntityExtractor:
    def __init__(self):
        self._init_natasha()

    def _init_natasha(self) -> None:
        """Инициализация всех компонентов Natasha."""
        self.segmenter = Segmenter()
        self.morph_vocab = MorphVocab()
        self.emb = NewsEmbedding()
        self.morph_tagger = NewsMorphTagger(self.emb)
        self.syntax_parser = NewsSyntaxParser(self.emb)
        self.ner_tagger = NewsNERTagger(self.emb)

        self.names_extractor = NamesExtractor(self.morph_vocab)
        self.dates_extractor = DatesExtractor(self.morph_vocab)
        self.money_extractor = MoneyExtractor(self.morph_vocab)
        self.addr_extractor = AddrExtractor(self.morph_vocab)

    def extract(self, text: str) -> list[ExtractedEntity]:
        """
        Извлечь все приватные сущности из текста.

        Args:
            text: Входной текст на русском языке.

        Returns:
            Список объектов ExtractedEntity, отсортированных по позиции.
        """
        if not text or not text.strip():
            return []

        entities: list[ExtractedEntity] = []

        entities.extend(self._extract_persons(text))
        entities.extend(self._extract_dates(text))
        entities.extend(self._extract_locations(text))
        entities.extend(self._extract_money(text))

        entities.sort(key=lambda e: e.start)
        return entities

    def _extract_persons(self, text: str) -> list[ExtractedEntity]:
        """Извлечение личных имён через NER + нормализация через NamesExtractor."""
        entities = []

        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        doc.parse_syntax(self.syntax_parser)
        doc.tag_ner(self.ner_tagger)

        for span in doc.spans:
            span.normalize(self.morph_vocab)

        ner_persons = {
            (span.start, span.stop): span for span in doc.spans if span.type == "PER"
        }

        name_details: dict[tuple, dict] = {}
        for match in self.names_extractor(text):
            fact = match.fact
            details = {}
            if fact.first:
                details["first"] = fact.first
            if fact.last:
                details["last"] = fact.last
            if fact.middle:
                details["middle"] = fact.middle
            name_details[(match.start, match.stop)] = details

        for (start, stop), span in ner_persons.items():
            details = name_details.get((start, stop), {})
            entities.append(
                ExtractedEntity(
                    entity_type="PERSON",
                    text=text[start:stop],
                    start=start,
                    stop=stop,
                    normal_form=span.normal,
                    details=details,
                )
            )

        return entities

    def _extract_dates(self, text: str) -> list[ExtractedEntity]:
        """Извлечение дат."""
        entities = []

        for match in self.dates_extractor(text):
            fact = match.fact
            details = {}
            if fact.year:
                details["year"] = fact.year
            if fact.month:
                details["month"] = fact.month
            if fact.day:
                details["day"] = fact.day

            parts = []
            if fact.day:
                parts.append(str(fact.day))
            if fact.month:
                parts.append(str(fact.month))
            if fact.year:
                parts.append(str(fact.year))
            normal_form = ".".join(parts) if parts else None

            entities.append(
                ExtractedEntity(
                    entity_type="DATE",
                    text=text[match.start : match.stop],
                    start=match.start,
                    stop=match.stop,
                    normal_form=normal_form,
                    details=details,
                )
            )

        return entities

    def _extract_locations(self, text: str) -> list[ExtractedEntity]:
        """Извлечение мест через NER + адресов через AddrExtractor."""
        entities = []
        seen_spans: set[tuple[int, int]] = set()

        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        doc.parse_syntax(self.syntax_parser)
        doc.tag_ner(self.ner_tagger)

        for span in doc.spans:
            span.normalize(self.morph_vocab)

        for span in doc.spans:
            if span.type == "LOC":
                key = (span.start, span.stop)
                seen_spans.add(key)
                entities.append(
                    ExtractedEntity(
                        entity_type="LOCATION",
                        text=text[span.start : span.stop],
                        start=span.start,
                        stop=span.stop,
                        normal_form=span.normal,
                    )
                )

        for match in self.addr_extractor(text):
            key = (match.start, match.stop)
            if key in seen_spans:
                continue

            fact = match.fact
            details = {}
            parts = []

            for attr in ("country", "region", "city", "street", "house"):
                value = getattr(fact, attr, None)
                if value:
                    details[attr] = value
                    parts.append(str(value))

            entities.append(
                ExtractedEntity(
                    entity_type="LOCATION",
                    text=text[match.start : match.stop],
                    start=match.start,
                    stop=match.stop,
                    normal_form=", ".join(parts) if parts else None,
                    details=details,
                )
            )

        return entities

    def _extract_money(self, text: str) -> list[ExtractedEntity]:
        """Извлечение цен и денежных сумм."""
        entities = []

        for match in self.money_extractor(text):
            fact = match.fact
            details = {}

            if fact.amount:
                details["amount"] = fact.amount
            if fact.currency:
                details["currency"] = fact.currency

            normal_parts = []
            if fact.amount:
                normal_parts.append(str(fact.amount))
            if fact.currency:
                normal_parts.append(fact.currency)
            normal_form = " ".join(normal_parts) if normal_parts else None

            entities.append(
                ExtractedEntity(
                    entity_type="MONEY",
                    text=text[match.start : match.stop],
                    start=match.start,
                    stop=match.stop,
                    normal_form=normal_form,
                    details=details,
                )
            )

        return entities

    def extract_persons(self, text: str) -> list[ExtractedEntity]:
        return [e for e in self.extract(text) if e.entity_type == "PERSON"]

    def extract_dates(self, text: str) -> list[ExtractedEntity]:
        return [e for e in self.extract(text) if e.entity_type == "DATE"]

    def extract_locations(self, text: str) -> list[ExtractedEntity]:
        return [e for e in self.extract(text) if e.entity_type == "LOCATION"]

    def extract_money(self, text: str) -> list[ExtractedEntity]:
        return [e for e in self.extract(text) if e.entity_type == "MONEY"]

    def extract_as_dict(self, text: str) -> dict[str, list[ExtractedEntity]]:
        """Вернуть сущности, сгруппированные по типу."""
        result: dict[str, list[ExtractedEntity]] = {
            "PERSON": [],
            "DATE": [],
            "LOCATION": [],
            "MONEY": [],
        }
        for entity in self.extract(text):
            result[entity.entity_type].append(entity)
        return result

    def anonymize(self, text: str, placeholder: str = "[СКРЫТО]") -> str:
        """
        Анонимизировать текст, заменив все найденные сущности
        на placeholder.
        """
        entities = self.extract(text)
        for entity in sorted(entities, key=lambda e: e.start, reverse=True):
            text = text[: entity.start] + placeholder + text[entity.stop :]
        return text
