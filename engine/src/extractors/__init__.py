from .models import Entity, Span
from .natasha import dates, locations, money, persons  # noqa: F401
from .pipeline import ExtractionPipeline
from .regex import email, inn, passport, phone, snils  # noqa: F401
from .registry import registry

__all__ = ["ExtractionPipeline", "registry", "Entity", "Span"]
