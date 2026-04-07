from __future__ import annotations

from functools import cached_property

from natasha import (
    AddrExtractor,
    DatesExtractor,
    MoneyExtractor,
    MorphVocab,
    NamesExtractor,
    NewsEmbedding,
    NewsMorphTagger,
    NewsNERTagger,
    NewsSyntaxParser,
    Segmenter,
)


class NatashaComponents:
    """
    Синглтон-контейнер компонентов Natasha.
    Модели загружаются лениво и переиспользуются всеми экстракторами.
    """

    _instance: NatashaComponents | None = None

    def __new__(cls) -> NatashaComponents:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @cached_property
    def segmenter(self) -> Segmenter:
        return Segmenter()

    @cached_property
    def morph_vocab(self) -> MorphVocab:
        return MorphVocab()

    @cached_property
    def emb(self) -> NewsEmbedding:
        return NewsEmbedding()

    @cached_property
    def morph_tagger(self) -> NewsMorphTagger:
        return NewsMorphTagger(self.emb)

    @cached_property
    def syntax_parser(self) -> NewsSyntaxParser:
        return NewsSyntaxParser(self.emb)

    @cached_property
    def ner_tagger(self) -> NewsNERTagger:
        return NewsNERTagger(self.emb)

    @cached_property
    def names_extractor(self) -> NamesExtractor:
        return NamesExtractor(self.morph_vocab)

    @cached_property
    def dates_extractor(self) -> DatesExtractor:
        return DatesExtractor(self.morph_vocab)

    @cached_property
    def money_extractor(self) -> MoneyExtractor:
        return MoneyExtractor(self.morph_vocab)

    @cached_property
    def addr_extractor(self) -> AddrExtractor:
        return AddrExtractor(self.morph_vocab)

    def make_doc(self, text: str):
        from natasha import Doc

        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        doc.parse_syntax(self.syntax_parser)
        doc.tag_ner(self.ner_tagger)
        for span in doc.spans:
            span.normalize(self.morph_vocab)
        return doc


class BaseNatashaExtractor:
    """Базовый класс для Natasha-экстракторов — предоставляет доступ к компонентам."""

    def __init__(self) -> None:
        self._natasha = NatashaComponents()
