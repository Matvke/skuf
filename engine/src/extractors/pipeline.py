from __future__ import annotations

from .base import BaseExtractor
from .models import Entity
from .registry import registry


class ExtractionPipeline:
    """
    Запускает набор экстракторов и агрегирует результаты.

    Пример:
        pipeline = ExtractionPipeline.from_registry()
        results  = pipeline.run(text)
    """

    def __init__(self, extractors: list[BaseExtractor]) -> None:
        self._extractors = extractors

    @classmethod
    def from_registry(cls, *names: str) -> ExtractionPipeline:
        """Создать пайплайн из зарегистрированных экстракторов."""
        extractors = (
            registry.instantiate(*names) if names else registry.instantiate_all()
        )
        return cls(extractors)

    def run(
        self,
        text: str,
        *,
        remove_overlaps: bool = True,
    ) -> list[Entity]:
        """
        Запустить все экстракторы.

        Args:
            text:             Входной текст.
            remove_overlaps:  Убрать пересекающиеся сущности (оставить с большей уверенностью).
        """
        entities: list[Entity] = []
        for extractor in self._extractors:
            entities.extend(extractor.extract(text))

        entities.sort(key=lambda e: e.span.start)

        if remove_overlaps:
            entities = self._resolve_overlaps(entities)

        return entities

    def anonymize(
        self,
        text: str,
        placeholder: str = "[СКРЫТО]",
        *,
        remove_overlaps: bool = True,
    ) -> str:
        """Заменить все найденные сущности на placeholder."""
        entities = self.run(text, remove_overlaps=remove_overlaps)
        for entity in sorted(entities, key=lambda e: e.span.start, reverse=True):
            s, e = entity.span.start, entity.span.stop
            text = text[:s] + placeholder + text[e:]
        return text

    def group_by_type(self, text: str) -> dict[str, list[Entity]]:
        """Сгруппировать результаты по типу сущности."""
        result: dict[str, list[Entity]] = {}
        for entity in self.run(text):
            result.setdefault(entity.entity_type, []).append(entity)
        return result

    @staticmethod
    def _resolve_overlaps(entities: list[Entity]) -> list[Entity]:
        """Убрать пересечения: при конфликте побеждает более уверенный экстрактор."""
        result: list[Entity] = []
        for candidate in entities:
            overlapping = [e for e in result if e.span.overlaps(candidate.span)]
            if not overlapping:
                result.append(candidate)
            elif candidate.confidence > max(e.confidence for e in overlapping):
                for e in overlapping:
                    result.remove(e)
                result.append(candidate)
        return sorted(result, key=lambda e: e.span.start)
