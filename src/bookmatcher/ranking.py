from __future__ import annotations

from dataclasses import dataclass

from .models import Book, CatalogRecord


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    record: CatalogRecord
    year_distance: int | None


def rank_candidates(
    book: Book,
    candidates: list[CatalogRecord],
    top_k: int | None = None,
) -> list[RankedCandidate]:
    """
    Rank catalog candidates by absolute publication-year distance.

    Candidates without a usable year are placed at the end.
    """

    book_year = _parse_year(book.year_raw)

    ranked = [
        RankedCandidate(
            record=candidate,
            year_distance=_year_distance(
                book_year,
                candidate.year,
            ),
        )
        for candidate in candidates
    ]

    ranked.sort(
        key=lambda candidate: (
            candidate.year_distance is None,
            candidate.year_distance
            if candidate.year_distance is not None
            else float("inf"),
        )
    )

    if top_k is not None:
        if top_k < 1:
            raise ValueError("top_k must be >= 1")

        ranked = ranked[:top_k]

    return ranked


def _year_distance(
    source_year: int | None,
    candidate_year: int | None,
) -> int | None:
    if source_year is None or candidate_year is None:
        return None

    return abs(source_year - candidate_year)


def _parse_year(
    value: int | float | str | None,
) -> int | None:
    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if value != value:  # NaN
            return None

        return int(value)

    value = str(value).strip()

    if not value:
        return None

    try:
        return int(float(value))
    except ValueError:
        return None