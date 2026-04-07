import re

from ..registry import registry
from .base_regex import BaseRegexExtractor, RegexPattern


@registry.register
class PassportExtractor(BaseRegexExtractor):
    """
    Извлекает серию и номер паспорта РФ.

    Форматы:
        - «серия 4507 номер 123456»
        - «паспорт 45 07 123456»
        - «45 07 123456»
        - «4507 123456»
    """

    name = "passport"
    entity_types = ("PASSPORT",)

    patterns = [
        RegexPattern(
            pattern=(
                r"(?:паспорт\s+|серия\s+)?"
                r"(?P<series>\d{2}[\s\-]?\d{2})"
                r"[\s\-,]*"
                r"(?:номер\s+|№\s*)?"
                r"(?P<number>\d{6})"
            ),
            description="Серия и номер паспорта РФ",
        ),
    ]

    def normalize(self, match: re.Match) -> str:
        series = re.sub(r"\D", "", match.group("series"))
        number = match.group("number")
        return f"{series[:2]} {series[2:]} {number}"

    def build_details(self, match: re.Match) -> dict:
        series = re.sub(r"\D", "", match.group("series"))
        return {
            "series": f"{series[:2]} {series[2:]}",
            "number": match.group("number"),
        }
