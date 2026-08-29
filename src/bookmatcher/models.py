from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Book:
    """Minimal representation needed for the later catalog lookup."""

    source_row: int
    author: str | None
    title: str | None
    year_raw: int | float | str | None
    annotation_raw: str | None = None
