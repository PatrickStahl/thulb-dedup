from __future__ import annotations

from dataclasses import dataclass
import re

SEARCH_TITLE_COLUMN = "Such-Titel"
VOLUME_COLUMN = "Band"


@dataclass(frozen=True, slots=True)
class CleanedTitle:
    search_title: str
    volume: str | None


_VOLUME_VALUE_RE = r"(?:\d+(?:\s*[,./-]\s*\d+)?|[IVXLCDM]+)"

_VOLUME_AFTER_LABEL_RE = re.compile(
    rf"""
    \b
    (?:
        band
        | bd\.?
        | teil
        | heft
        | folge
        | nr\.?
    )
    \s*
    [:.\-]?
    \s*
    (?P<volume>{_VOLUME_VALUE_RE})
    \b
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)

_VOLUME_BEFORE_LABEL_RE = re.compile(
    rf"""
    \b
    (?P<volume>{_VOLUME_VALUE_RE})
    \s*
    \.?
    \s*
    (?:
        band
        | bd\.?
        | teil
        | heft
        | folge
        | nr\.?
    )
    \b
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)


# Parenthesized bibliographic metadata such as:
#
#   (5. Aufl.)
#   (2. Band)
#   (Bd. 3)
#   (Teil 1)
#
# We deliberately only remove parentheses containing known
# bibliographic markers. Other parentheses may be part of the title.
_PARENTHESIZED_METADATA_RE = re.compile(
    r"""
    \(
        [^)]*
        \b
        (?:
            aufl(?:age)?
            | band
            | bd
            | teil
            | heft
            | folge
            | nr
        )
        \.?
        \b
        [^)]*
    \)
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)


# Inline edition information such as:
#
#   5. Aufl.
#   3.Auflage
#
_INLINE_EDITION_RE = re.compile(
    r"""
    \b
    \d+
    \s*
    \.
    \s*
    aufl(?:age)?
    \.?
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)


# Metadata at the end of a title:
#
#   Einführung in die Sprachwissenschaft Band 1
#   Foo Teil II
#   Bar Heft 4
#
# We only remove these expressions at the END of the title.
_TRAILING_VOLUME_RE = re.compile(
    r"""
    [\s,;:\-–—]+
    (?:
        band
        | bd\.?
        | teil
        | heft
        | folge
        | nr\.?
    )
    \s*
    (?:
        \d+
        | [IVXLCDM]+
    )
    \s*
    $
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_title_for_query(
    title: str,
) -> str:
    """
    Normalize a local title for K10plus retrieval.

    The normalization is deliberately conservative. It removes obvious
    edition/volume metadata while preserving the actual bibliographic
    title as far as possible.

    Examples:
        "Althochdeutsches Lesebuch (11. Aufl.)"
            -> "Althochdeutsches Lesebuch"

        "Einführung in die Sprachwissenschaft Band 1"
            -> "Einführung in die Sprachwissenschaft"

        "Germania Romana I"
            -> "Germania Romana I"
    """

    return clean_title_for_search(title).search_title


def clean_title_for_search(title: str) -> CleanedTitle:
    """Create an inspectable title/volume pair for catalog lookup.

    Numeric volume markers are removed from the search title and normalized for
    ``pica.tmb`` queries. The parser deliberately ignores purely textual volume
    phrases. In strings such as ``V.Band 12., 13. und 14. Lieferung``, the roman
    numeral directly attached to ``Band`` is the volume; later delivery numbers
    are not treated as volumes.
    """
    title = _normalize_whitespace(title)
    volume_match = _find_volume_match(title)
    volume = _normalize_volume(volume_match.group("volume")) if volume_match else None

    if volume_match is not None:
        title = _remove_volume_phrase(title, volume_match)

    title = _PARENTHESIZED_METADATA_RE.sub(
        "",
        title,
    )

    title = _INLINE_EDITION_RE.sub(
        "",
        title,
    )

    title = _TRAILING_VOLUME_RE.sub(
        "",
        title,
    )

    # Removing metadata may leave extra spaces or separators at the end.
    title = title.strip(" ,;:-–—")

    return CleanedTitle(
        search_title=_normalize_whitespace(title),
        volume=volume,
    )


def extract_volume(value: str | None) -> str | None:
    if not value:
        return None

    value = _normalize_whitespace(value)
    if re.fullmatch(_VOLUME_VALUE_RE, value, flags=re.IGNORECASE):
        return _normalize_volume(value)

    match = _find_volume_match(value)
    if match is None:
        return None

    return _normalize_volume(match.group("volume"))


def normalize_author_for_query(
    author: str,
) -> str:
    """
    Reduce an author field to a robust person query.

    For the normal spreadsheet format we primarily use the surname.

    Examples:
        "Admoni, Vladimir"
            -> "Admoni"

        "von Bahder, Karl"
            -> "von Bahder"

        "Frings, Theodor und Müller, Gertraud"
            -> "Frings"

        "Deutscher Abend in Halle"
            -> "Deutscher Abend in Halle"
    """

    author = _normalize_whitespace(author)

    if "," in author:
        surname, _ = author.split(
            ",",
            maxsplit=1,
        )

        return surname.strip()

    return author


def _normalize_whitespace(
    value: str,
) -> str:
    return _WHITESPACE_RE.sub(
        " ",
        value,
    ).strip()


def _find_volume_match(title: str) -> re.Match[str] | None:
    before_match = _VOLUME_BEFORE_LABEL_RE.search(title)
    after_match = _VOLUME_AFTER_LABEL_RE.search(title)

    if before_match and after_match:
        return min(
            before_match,
            after_match,
            key=lambda match: match.start(),
        )

    return before_match or after_match


def _remove_volume_phrase(title: str, match: re.Match[str]) -> str:
    if _is_inside_parentheses(title, match.start(), match.end()):
        opening = title.rfind("(", 0, match.start())
        closing = title.find(")", match.end())
        if opening != -1 and closing != -1:
            return f"{title[:opening]} {title[closing + 1:]}"

    return title[: match.start()]


def _is_inside_parentheses(title: str, start: int, end: int) -> bool:
    opening = title.rfind("(", 0, start)
    closing_before = title.rfind(")", 0, start)
    closing_after = title.find(")", end)

    return opening > closing_before and closing_after != -1


def _normalize_volume(value: str) -> str:
    value = re.sub(r"\s+", "", value).strip(".,;:")

    if re.fullmatch(r"[IVXLCDM]+", value, flags=re.IGNORECASE):
        return str(_roman_to_int(value))

    return value


def _roman_to_int(value: str) -> int:
    values = {
        "I": 1,
        "V": 5,
        "X": 10,
        "L": 50,
        "C": 100,
        "D": 500,
        "M": 1000,
    }
    total = 0
    previous = 0

    for char in reversed(value.upper()):
        number = values[char]
        if number < previous:
            total -= number
        else:
            total += number
            previous = number

    return total
