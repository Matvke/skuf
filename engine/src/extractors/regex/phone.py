import re

from ..registry import registry
from .base_regex import BaseRegexExtractor, RegexPattern


@registry.register
class PhoneExtractor(BaseRegexExtractor):
    """Номера телефонов в различных форматах."""

    name = "phone"
    entity_types = ("PHONE",)

    patterns = [
        RegexPattern(
            pattern=(
                r"(?:\+7|8)"
                r"[\s\-\(]*(?P<code>\d{3})[\s\-\)]*"
                r"(?P<part1>\d{3})[\s\-]*"
                r"(?P<part2>\d{2})[\s\-]*"
                r"(?P<part3>\d{2})"
            ),
            description="Российский номер телефона",
        ),
    ]

    def normalize(self, match: re.Match) -> str:
        code = match.group("code")
        part1 = match.group("part1")
        part2 = match.group("part2")
        part3 = match.group("part3")
        return f"+7 ({code}) {part1}-{part2}-{part3}"

    def build_details(self, match: re.Match) -> dict:
        return {
            "country_code": "+7",
            "area_code": match.group("code"),
            "number": (
                f"{match.group('part1')}{match.group('part2')}{match.group('part3')}"
            ),
        }
