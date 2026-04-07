from extractors.models import Entity, Span
from extractors.natasha.dates import DateExtractor
from extractors.natasha.locations import LocationExtractor


class TestNatashaDateExtractors:
    def test_many_dates(self):
        extr = DateExtractor()
        expected = [
            Entity(
                entity_type="DATE",
                text="15 марта 2023 года",
                span=Span(start=19, stop=37),
                normal_form="15.3.2023",
                details={"year": 2023, "month": 3, "day": 15},
                source="date",
            ),
            Entity(
                entity_type="DATE",
                text="22.06.2023",
                span=Span(start=62, stop=72),
                normal_form="22.6.2023",
                details={"year": 2023, "month": 6, "day": 22},
                source="date",
            ),
        ]
        entities = extr.extract(
            "Проект был запущен 15 марта 2023 года. Первый этап завершился 22.06.2023."
        )
        for i, entity in enumerate(entities):
            assert entity == expected[i]

    def test_full_date(self):
        extr = DateExtractor()
        expected = [
            Entity(
                entity_type="DATE",
                text="15 марта 2023 года",
                span=Span(start=19, stop=37),
                normal_form="15.3.2023",
                details={"year": 2023, "month": 3, "day": 15},
                source="date",
            )
        ]
        entities = extr.extract("Проект был запущен 15 марта 2023 года.")
        for i, entity in enumerate(entities):
            assert entity == expected[i]

    def test_short_date(self):
        extr = DateExtractor()
        expected = [
            Entity(
                entity_type="DATE",
                text="22.06.2023",
                span=Span(start=23, stop=33),
                normal_form="22.6.2023",
                details={"year": 2023, "month": 6, "day": 22},
                source="date",
            )
        ]
        entities = extr.extract("Первый этап завершился 22.06.2023.")
        for i, entity in enumerate(entities):
            assert entity == expected[i]

    def test_day_month(self):
        extr = DateExtractor()
        expected = [
            Entity(
                entity_type="DATE",
                text="22 мая",
                span=Span(start=14, stop=20),
                normal_form="22.5",
                details={"month": 5, "day": 22},
                source="date",
            )
        ]
        entities = extr.extract("День рождения 22 мая.")
        for i, entity in enumerate(entities):
            assert entity == expected[i]

    def test_year(self):
        extr = DateExtractor()
        expected = [
            Entity(
                entity_type="DATE",
                text="1957 года",
                span=Span(start=14, stop=23),
                normal_form="1957",
                details={"year": 1957},
                source="date",
            )
        ]
        entities = extr.extract("День рождения 1957 года.")
        for i, entity in enumerate(entities):
            assert entity == expected[i]


class TestNatashaLocationExtractor:
    def test_city(self):
        extr = LocationExtractor()
        expected = [
            Entity(
                entity_type="LOCATION",
                text="России",
                span=Span(start=32, stop=38),
                normal_form="Россия",
                details={},
                source="location",
            ),
            Entity(
                entity_type="LOCATION",
                text="Казахстан",
                span=Span(start=51, stop=60),
                normal_form="Казахстан",
                details={},
                source="location",
            ),
            Entity(
                entity_type="LOCATION",
                text="Алматы",
                span=Span(start=62, stop=68),
                normal_form="Алматы",
                details={},
                source="location",
            ),
        ]
        entities = extr.extract(
            "Доставка осуществляется по всей России, а так же в Казахстан, Алматы"
        )
        for i, entity in enumerate(entities):
            assert entity == expected[i]
