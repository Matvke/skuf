from natasha import (
    Doc,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    NewsNERTagger,
    Segmenter,
)


class NameExtractor:
    def __init__(self):
        self.segmenter = Segmenter()
        self.morph_vocab = MorphVocab()
        self.emb = NewsEmbedding()
        self.morph_tagger = NewsMorphTagger(self.emb)
        self.ner_tagger = NewsNERTagger(self.emb)

    def extract(self, text):
        """Извлекает все имена из текста"""
        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        doc.tag_ner(self.ner_tagger)

        names = []
        for span in doc.spans:
            if span.type == "PER":
                span.normalize(self.morph_vocab)
                names.append(span.normal)

        return names

    def extract_with_positions(self, text):
        """Извлекает имена с позициями в тексте"""
        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        doc.tag_ner(self.ner_tagger)

        results = []
        for span in doc.spans:
            if span.type == "PER":
                span.normalize(self.morph_vocab)
                results.append(
                    {
                        "name": span.normal,
                        "original": span.text,
                        "start": span.start,
                        "end": span.stop,
                    }
                )

        return results
