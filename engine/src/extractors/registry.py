from typing import Type

from .base import BaseExtractor


class ExtractorRegistry:
    """
    Хранит все доступные классы экстракторов.
    Позволяет регистрировать новые через декоратор @registry.register.
    """

    def __init__(self) -> None:
        self._extractors: dict[str, Type[BaseExtractor]] = {}

    def register(self, cls: Type[BaseExtractor]) -> Type[BaseExtractor]:
        """Декоратор регистрации. Использование: @registry.register"""
        if not cls.name:
            raise ValueError(f"{cls} должен определить атрибут `name`")
        self._extractors[cls.name] = cls
        return cls

    def get(self, name: str) -> Type[BaseExtractor]:
        if name not in self._extractors:
            raise KeyError(
                f"Экстрактор {name!r} не найден. Доступные: {list(self._extractors)}"
            )
        return self._extractors[name]

    def all_names(self) -> list[str]:
        return list(self._extractors)

    def instantiate_all(self) -> list[BaseExtractor]:
        """Создать экземпляры всех зарегистрированных экстракторов."""
        return [cls() for cls in self._extractors.values()]

    def instantiate(self, *names: str) -> list[BaseExtractor]:
        """Создать экземпляры только выбранных экстракторов."""
        return [self.get(name)() for name in names]


registry = ExtractorRegistry()
