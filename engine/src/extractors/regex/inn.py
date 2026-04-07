import re

from ..registry import registry
from .base_regex import BaseRegexExtractor, RegexPattern


@registry.register
class InnExtractor(BaseRegexExtractor):
    """
    Извлекает ИНН физических лиц (12 цифр) и юридических лиц (10 цифр).
    Выполняет проверку контрольной суммы.
    """

    name = "inn"
    entity_types = ("INN",)

    patterns = [
        RegexPattern(
            pattern=r"(?:ИНН\s*[:№]?\s*)?(?P<inn>\d{10}|\d{12})",
            description="ИНН физлица (12 цифр) или юрлица (10 цифр)",
        ),
    ]

    # Коэффициенты для проверки контрольной суммы
    _COEFFICIENTS_12_N1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    _COEFFICIENTS_12_N2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    _COEFFICIENTS_10 = [2, 4, 10, 3, 5, 9, 4, 6, 8]

    def validate(self, match: re.Match) -> bool:
        inn = match.group("inn")
        if len(inn) == 10:
            return self._check_10(inn)
        if len(inn) == 12:
            return self._check_12(inn)
        return False

    def normalize(self, match: re.Match) -> str:
        return match.group("inn")

    def build_details(self, match: re.Match) -> dict:
        inn = match.group("inn")
        return {
            "inn": inn,
            "type": "individual" if len(inn) == 12 else "legal_entity",
        }

    # --- Контрольная сумма ---

    @staticmethod
    def _control_digit(digits: list[int], coefficients: list[int]) -> int:
        return sum(d * c for d, c in zip(digits, coefficients)) % 11 % 10

    def _check_10(self, inn: str) -> bool:
        digits = list(map(int, inn))
        return self._control_digit(digits[:9], self._COEFFICIENTS_10) == digits[9]

    def _check_12(self, inn: str) -> bool:
        digits = list(map(int, inn))
        n1 = self._control_digit(digits[:10], self._COEFFICIENTS_12_N1)
        n2 = self._control_digit(digits[:11], self._COEFFICIENTS_12_N2)
        return n1 == digits[10] and n2 == digits[11]
