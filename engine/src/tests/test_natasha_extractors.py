from extractors.models import Entity, Span
from extractors.natasha.dates import DateExtractor
from extractors.natasha.locations import LocationExtractor
from extractors.natasha.money import MoneyExtractor
from extractors.natasha.persons import PersonExtractor


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
    def test_city_country(self):
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


class TestNatashaMoneyExtractor:
    def test_many_money(self):
        extr = MoneyExtractor()
        expected = [
            Entity(
                entity_type="MONEY",
                text="1 299 ₽",
                span=Span(start=21, stop=28),
                normal_form="1299 RUB",
                details={"amount": 1299.0, "currency": "RUB"},
                source="money",
            ),
            Entity(
                entity_type="MONEY",
                text="1 558,80 руб.",
                span=Span(start=38, stop=51),
                normal_form="1558.8 RUB",
                details={"amount": 1558.8, "currency": "RUB"},
                source="money",
            ),
            Entity(
                entity_type="MONEY",
                text="$49.99",
                span=Span(start=60, stop=66),
                normal_form="49.99 USD",
                details={"amount": 49.99, "currency": "USD"},
                source="money",
            ),
            Entity(
                entity_type="MONEY",
                text="€85",
                span=Span(start=68, stop=71),
                normal_form="85 EUR",
                details={"amount": 85.0, "currency": "EUR"},
                source="money",
            ),
        ]
        entities = extr.extract(
            "Стоимость подписки — 1 299 ₽, с НДС — 1 558,80 руб. Доп. услуги: $49.99, €85."
        )
        for i, entity in enumerate(entities):
            assert entity == expected[i]

    def test_rubles(self):
        extr = MoneyExtractor()
        expected = [
            Entity(
                entity_type="MONEY",
                text="3500 рублей",
                span=Span(start=0, stop=11),
                normal_form="3500 RUB",
                details={"amount": 3500.0, "currency": "RUB"},
                source="money",
            )
        ]
        entities = extr.extract("3500 рублей")
        for i, entity in enumerate(entities):
            assert entity == expected[i]

    def test_dollars(self):
        extr = MoneyExtractor()
        expected = [
            Entity(
                entity_type="MONEY",
                text="1000.50 USD",
                span=Span(start=0, stop=10),
                normal_form="1000.5 USD",
                details={"amount": 1000.5, "currency": "USD"},
                source="money",
            )
        ]
        entities = extr.extract("1000.50 USD")
        for i, entity in enumerate(entities):
            assert entity == expected[i]

    def test_euros_with_space(self):
        extr = MoneyExtractor()
        expected = [
            Entity(
                entity_type="MONEY",
                text="12 345 EUR",
                span=Span(start=0, stop=9),
                normal_form="12345 EUR",
                details={"amount": 12345.0, "currency": "EUR"},
                source="money",
            )
        ]
        entities = extr.extract("12 345 EUR")
        for i, entity in enumerate(entities):
            assert entity == expected[i]

    def test_millions(self):
        extr = MoneyExtractor()
        expected = [
            Entity(
                entity_type="MONEY",
                text="2.5 млн руб.",
                span=Span(start=0, stop=12),
                normal_form="2500000.0 RUB",
                details={"amount": 2500000.0, "currency": "RUB"},
                source="money",
            )
        ]
        entities = extr.extract("2.5 млн руб.")
        for i, entity in enumerate(entities):
            assert entity == expected[i]


class TestNatashaPersonExtractor:
    def test_many_names(self):
        extr = PersonExtractor()
        expected = [
            Entity(
                entity_type="PERSON",
                text="Иванов Дмитрий Олегович",
                span=Span(start=7, stop=30),
                normal_form="Иванов Дмитрий Олегович",
                details={},
                source="person",
            ),
            Entity(
                entity_type="PERSON",
                text="Елена Петровна Смирнова",
                span=Span(start=51, stop=74),
                normal_form="Елена Петровна Смирнова",
                details={},
                source="person",
            ),
            Entity(
                entity_type="PERSON",
                text="Александр К",
                span=Span(start=98, stop=109),
                normal_form="Александр К",
                details={},
                source="person",
            ),
            Entity(
                entity_type="PERSON",
                text="Мария",
                span=Span(start=126, stop=131),
                normal_form="Мария",
                details={},
                source="person",
            ),
            Entity(
                entity_type="PERSON",
                text="Джон Смит",
                span=Span(start=133, stop=142),
                normal_form="Джон Смит",
                details={},
                source="person",
            ),
        ]
        entities = extr.extract(
            "Клиент Иванов Дмитрий Олегович обратился. Оператор Елена Петровна Смирнова. Консультацию проводил Александр К. Также указаны: Мария, Джон Смит."
        )
        for i, entity in enumerate(entities):
            assert entity == expected[i]

    def test_full_name(self):
        extr = PersonExtractor()
        expected = [
            Entity(
                entity_type="PERSON",
                text="Иванов Иван Иванович",
                span=Span(start=0, stop=20),
                normal_form="Иванов Иван Иванович",
                details={},
                source="person",
            )
        ]
        entities = extr.extract("Иванов Иван Иванович")
        for i, entity in enumerate(entities):
            assert entity == expected[i]

    def test_name_with_initial(self):
        extr = PersonExtractor()
        expected = [
            Entity(
                entity_type="PERSON",
                text="Петров А. Б.",
                span=Span(start=0, stop=12),
                normal_form="Петров А. Б.",
                details={},
                source="person",
            )
        ]
        entities = extr.extract("Петров А. Б.")
        for i, entity in enumerate(entities):
            assert entity == expected[i]

    def test_short_name(self):
        extr = PersonExtractor()
        expected = [
            Entity(
                entity_type="PERSON",
                text="Мария",
                span=Span(start=0, stop=5),
                normal_form="Мария",
                details={},
                source="person",
            )
        ]
        entities = extr.extract("Мария")
        for i, entity in enumerate(entities):
            assert entity == expected[i]
