import pytest

from bookmatcher.normalization import (
    clean_title_for_search,
    extract_volume,
    normalize_author_for_query,
    normalize_title_for_query,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "Abriss der althochdeutschen Grammatik "
            "mit Berücksichtigung des Altsächsischen (5. Aufl.)",
            "Abriss der althochdeutschen Grammatik "
            "mit Berücksichtigung des Altsächsischen",
        ),
        (
            "Althochdeutsches Lesebuch (11. Aufl.)",
            "Althochdeutsches Lesebuch",
        ),
        (
            "Die Englische Sprache - "
            "ihre geschichtliche Entwicklung (2. Band)",
            "Die Englische Sprache - "
            "ihre geschichtliche Entwicklung",
        ),
        (
            "Einführung in die Sprachwissenschaft Band 1",
            "Einführung in die Sprachwissenschaft",
        ),
        (
            "Deutsche Grammatik 3. Aufl.",
            "Deutsche Grammatik",
        ),
        (
            "Germania Romana I",
            "Germania Romana I",
        ),
        (
            "Sprachbewegungen in der Pfalz - "
            "Richtungen und Schranken",
            "Sprachbewegungen in der Pfalz - "
            "Richtungen und Schranken",
        ),
    ],
)
def test_normalize_title(
    raw: str,
    expected: str,
) -> None:
    assert normalize_title_for_query(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "Admoni, Vladimir",
            "Admoni",
        ),
        (
            "von Bahder, Karl",
            "von Bahder",
        ),
        (
            "Frings, Theodor und Müller, Gertraud",
            "Frings",
        ),
        (
            "Bromm, Ernst/ Corell, Hans",
            "Bromm",
        ),
        (
            "Deutscher Abend in Halle",
            "Deutscher Abend in Halle",
        ),
    ],
)
def test_normalize_author(
    raw: str,
    expected: str,
) -> None:
    assert normalize_author_for_query(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected_title", "expected_volume"),
    [
        (
            "Deutsche Wortforschung in europäischen Bezügen Band 6,1",
            "Deutsche Wortforschung in europäischen Bezügen",
            "6,1",
        ),
        (
            "Sudetendeutscher Wortatlas Band III",
            "Sudetendeutscher Wortatlas",
            "3",
        ),
        (
            "Historische Grammatik der niederländischen Sprache I. Band: Einleitung",
            "Historische Grammatik der niederländischen Sprache",
            "1",
        ),
        (
            "Thüringisches Wörterbuch V.Band 12., 13. und 14. Lieferung",
            "Thüringisches Wörterbuch",
            "5",
        ),
        (
            "Wörterbuch Band: herablappen-kutzeln",
            "Wörterbuch Band: herablappen-kutzeln",
            None,
        ),
    ],
)
def test_clean_title_for_search_extracts_numeric_or_roman_volume(
    raw: str,
    expected_title: str,
    expected_volume: str | None,
) -> None:
    cleaned = clean_title_for_search(raw)

    assert cleaned.search_title == expected_title
    assert cleaned.volume == expected_volume


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("3", "3"),
        ("Bd. III", "3"),
        ("V.Band", "5"),
        ("Band: herablappen-kutzeln", None),
    ],
)
def test_extract_volume_accepts_raw_and_normalized_values(
    raw: str,
    expected: str | None,
) -> None:
    assert extract_volume(raw) == expected
