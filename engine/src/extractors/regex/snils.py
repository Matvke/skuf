import re

from ..registry import registry
from .base_regex import BaseRegexExtractor, RegexPattern


@registry.register
class SnilsExtractor(BaseRegexExtractor):
    """
    СНИЛС: XXX-XXX-XXX YY или XXXXXXXXXXY (11 цифр).
    Проверяет контрольную сумму.
    """

    name = "snils"
    entity_types = ("SNILS",)

    patterns = [
        RegexPattern(
            pattern=(
                r"(?:СНИЛС\s*[:№]?\s*)?"
                r"(?P<snils>"
                r"\d{3}[\s\-]\d{3}[\s\-]\d{3}[\s\-]\d{2}"  # XXX-XXX-XXX YY
                r"|\d{11}"  # XXXXXXXXXXYY
                r")"
            ),
            description="СНИЛС",
        ),
    ]

    def validate(self, match: re.Match) -> bool:
        digits = re.sub(r"\D", "", match.group("snils"))
        if len(digits) != 11:
            return False
        number = int(digits[:9])
        # Номера ≤ 001001998 не проверяются по контрольной сумме
        if number <= 1_001_998:
            return True
        return self._check(digits)

    def normalize(self, match: re.Match) -> str:
        d = re.sub(r"\D", "", match.group("snils"))
        return f"{d[0:3]}-{d[3:6]}-{d[6:9]} {d[9:11]}"

    def build_details(self, match: re.Match) -> dict:
        d = re.sub(r"\D", "", match.group("snils"))
        return {
            "number": f"{d[0:3]}-{d[3:6]}-{d[6:9]}",
            "control": d[9:11],
        }

    @staticmethod
    def _check(digits: str) -> bool:
        total = sum(int(digits[i]) * (9 - i) for i in range(9))
        remainder = total % 101
        control = int(digits[9:11])
        if remainder in (100, 101):
            return control == 0
        return remainder == control
