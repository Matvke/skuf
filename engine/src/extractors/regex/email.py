import re

from ..registry import registry
from .base_regex import BaseRegexExtractor, RegexPattern


@registry.register
class EmailExtractor(BaseRegexExtractor):
    """Email-адреса."""

    name = "email"
    entity_types = ("EMAIL",)

    patterns = [
        RegexPattern(
            pattern=r"(?P<local>[a-zA-Z0-9_.+\-]+)@(?P<domain>[a-zA-Z0-9\-]+(?:\.[a-zA-Z]{2,})+)",
            description="Email-адрес",
        ),
    ]

    def normalize(self, match: re.Match) -> str:
        return match.group(0).lower()

    def build_details(self, match: re.Match) -> dict:
        return {
            "local": match.group("local"),
            "domain": match.group("domain"),
        }
