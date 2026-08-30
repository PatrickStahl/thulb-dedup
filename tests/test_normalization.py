import pytest

from bookmatcher.normalization import (
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