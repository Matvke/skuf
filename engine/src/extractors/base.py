from abc import ABC, abstractmethod
from typing import Iterator

from .models import Entity


class BaseExtractor(ABC):
    name: str = ""

    entity_types: tuple[str, ...] = ()

    @abstractmethod
    def extract(self, text: str) -> Iterator[Entity]:
        """Извлечь сущности из текста. Возвращает итератор Entity."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
