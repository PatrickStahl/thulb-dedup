from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import Iterable

from .k10plus import K10PlusClient, K10PlusError
from .models import Book, CatalogRecord
from .ranking import rank_candidates


AUTHOR_COLUMN = "Autor/Herausgeber"
YEAR_COLUMN = "Erscheinungsjahr"
TITLE_COLUMN = "Titel (Auflage)"
SOURCE_ROW_COLUMN = "Quellzeile"


RESULT_COLUMNS = [
    "match_status",
    "candidate_count",
    "candidate_rank",
    "candidate_ppn",
    "candidate_title",
    "candidate_authors",
    "candidate_year",
    "year_distance",
    "error",
]


def run_batch(
    input_path: str | Path,
    output_path: str | Path,
    *,
    client: K10PlusClient | None = None,
    top_k: int = 3,
    search_limit: int = 10,
    delay_seconds: float = 0.1,
    max_retries: int = 2,
) -> None:
    """
    Run K10plus lookup for every row in a CSV file.

    The input columns are preserved. For every catalog candidate,
    one output row is written.

    If no candidate is found, one row with match_status="no_results"
    is written.

    If title or author is missing, no API request is made and one row
    with match_status="missing_input" is written.
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    if top_k < 1:
        raise ValueError("top_k must be >= 1")

    if search_limit < top_k:
        raise ValueError("search_limit must be >= top_k")

    if delay_seconds < 0:
        raise ValueError("delay_seconds must be >= 0")

    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")

    client = client or K10PlusClient()

    rows, input_columns = _read_csv(input_path)

    _validate_columns(input_columns)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_columns = [
        *input_columns,
        *RESULT_COLUMNS,
    ]

    # In-memory cache for duplicate title/author combinations.
    cache: dict[
        tuple[str, str, int],
        list[CatalogRecord],
    ] = {}

    with output_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=output_columns,
        )

        writer.writeheader()

        total = len(rows)

        for index, row in enumerate(
            rows,
            start=1,
        ):
            source_row = row.get(
                SOURCE_ROW_COLUMN,
                "",
            )

            title = _clean_value(
                row.get(TITLE_COLUMN)
            )
            author = _clean_value(
                row.get(AUTHOR_COLUMN)
            )
            year = _clean_value(
                row.get(YEAR_COLUMN)
            )

            print(
                f"[{index}/{total}] "
                f"Quellzeile {source_row}: "
                f"{author or '<kein Autor>'} - "
                f"{title or '<kein Titel>'}"
            )

            if not title or not author:
                _write_result(
                    writer,
                    row,
                    status="missing_input",
                    error=(
                        "Titel oder Autor fehlt; "
                        "keine K10plus-Anfrage durchgeführt."
                    ),
                )
                continue

            book = Book(
                source_row=_parse_source_row(
                    source_row
                ),
                author=author,
                title=title,
                year_raw=year,
            )

            cache_key = (
                title,
                author,
                search_limit,
            )

            try:
                if cache_key in cache:
                    records = cache[cache_key]

                else:
                    records = _search_with_retries(
                        client=client,
                        title=title,
                        author=author,
                        limit=search_limit,
                        max_retries=max_retries,
                    )

                    cache[cache_key] = records

                    if delay_seconds:
                        time.sleep(delay_seconds)

            except K10PlusError as exc:
                print(
                    f"  -> ERROR: {exc}"
                )

                _write_result(
                    writer,
                    row,
                    status="error",
                    error=str(exc),
                )
                continue

            if not records:
                print("  -> keine Treffer")

                _write_result(
                    writer,
                    row,
                    status="no_results",
                    candidate_count=0,
                )
                continue

            ranked = rank_candidates(
                book,
                records,
                top_k=top_k,
            )

            print(
                f"  -> {len(records)} Treffer, "
                f"{len(ranked)} ausgegeben"
            )

            for rank, candidate in enumerate(
                ranked,
                start=1,
            ):
                record = candidate.record

                _write_result(
                    writer,
                    row,
                    status="ok",
                    candidate_count=len(records),
                    candidate_rank=rank,
                    candidate_ppn=record.ppn,
                    candidate_title=record.title,
                    candidate_authors=" | ".join(
                        record.authors
                    ),
                    candidate_year=record.year,
                    year_distance=(
                        candidate.year_distance
                    ),
                )


def _search_with_retries(
    *,
    client: K10PlusClient,
    title: str,
    author: str,
    limit: int,
    max_retries: int,
) -> list[CatalogRecord]:
    """
    Retry transient K10plus errors with a small exponential backoff.
    """

    attempts = max_retries + 1

    for attempt in range(attempts):
        try:
            return client.search(
                title=title,
                author=author,
                limit=limit,
            )

        except K10PlusError:
            if attempt == attempts - 1:
                raise

            wait_seconds = 2**attempt

            print(
                f"  -> Anfrage fehlgeschlagen, "
                f"Retry in {wait_seconds}s"
            )

            time.sleep(wait_seconds)

    # Only here for type checkers.
    raise RuntimeError(
        "unreachable"
    )


def _read_csv(
    path: Path,
) -> tuple[
    list[dict[str, str]],
    list[str],
]:
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(
                f"CSV file has no header: {path}"
            )

        columns = list(reader.fieldnames)
        rows = list(reader)

    return rows, columns


def _validate_columns(
    columns: Iterable[str],
) -> None:
    columns = set(columns)

    required = {
        SOURCE_ROW_COLUMN,
        AUTHOR_COLUMN,
        YEAR_COLUMN,
        TITLE_COLUMN,
    }

    missing = required - columns

    if missing:
        missing_text = ", ".join(
            sorted(missing)
        )

        raise ValueError(
            f"Missing required CSV columns: "
            f"{missing_text}"
        )


def _write_result(
    writer: csv.DictWriter,
    source_row: dict[str, str],
    *,
    status: str,
    candidate_count: int | str = "",
    candidate_rank: int | str = "",
    candidate_ppn: str | None = "",
    candidate_title: str | None = "",
    candidate_authors: str = "",
    candidate_year: int | str | None = "",
    year_distance: int | str | None = "",
    error: str = "",
) -> None:
    output = dict(source_row)

    output.update(
        {
            "match_status": status,
            "candidate_count": candidate_count,
            "candidate_rank": candidate_rank,
            "candidate_ppn": (
                candidate_ppn or ""
            ),
            "candidate_title": (
                candidate_title or ""
            ),
            "candidate_authors": (
                candidate_authors
            ),
            "candidate_year": (
                ""
                if candidate_year is None
                else candidate_year
            ),
            "year_distance": (
                ""
                if year_distance is None
                else year_distance
            ),
            "error": error,
        }
    )

    writer.writerow(output)


def _clean_value(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    value = value.strip()

    return value or None


def _parse_source_row(
    value: str | None,
) -> int:
    if not value:
        return -1

    try:
        return int(value)
    except ValueError:
        return -1


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Query K10plus for books from a CSV "
            "and rank catalog candidates by year."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input CSV, e.g. output/annotiert.csv",
    )

    parser.add_argument(
        "output",
        type=Path,
        help=(
            "Output CSV, e.g. "
            "output/annotiert_matches.csv"
        ),
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of ranked candidates to export.",
    )

    parser.add_argument(
        "--search-limit",
        type=int,
        default=10,
        help=(
            "Maximum number of records requested "
            "from K10plus."
        ),
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help=(
            "Delay between uncached API requests "
            "in seconds."
        ),
    )

    args = parser.parse_args()

    run_batch(
        input_path=args.input,
        output_path=args.output,
        top_k=args.top_k,
        search_limit=args.search_limit,
        delay_seconds=args.delay,
    )


if __name__ == "__main__":
    main()