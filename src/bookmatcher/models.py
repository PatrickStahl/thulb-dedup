from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Book:
    """Minimal representation needed for the catalog lookup."""

    source_row: int
    author: str | None
    title: str | None
    year_raw: int | float | str | None
    annotation_raw: str | None = None


@dataclass(frozen=True, slots=True)
class CatalogRecord:
    """Bibliographic record returned by K10plus."""

    ppn: str | None
    title: str | None
    authors: tuple[str, ...]
    year: int | None
    raw_xml: str
    volume: str | None = None
