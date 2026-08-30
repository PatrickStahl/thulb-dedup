from __future__ import annotations

import re


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

    title = _normalize_whitespace(title)

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

    return _normalize_whitespace(title)


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