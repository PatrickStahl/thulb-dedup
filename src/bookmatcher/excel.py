from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from .models import Book

AUTHOR_COLUMN = "Autor/Herausgeber"
YEAR_COLUMN = "Erscheinungsjahr"
TITLE_COLUMN = "Titel (Auflage)"
ANNOTATION_COLUMN = "Anzahl des Exemplares in Thulb"
SOURCE_ROW_COLUMN = "Quellzeile"

REQUIRED_COLUMNS = {
    AUTHOR_COLUMN,
    YEAR_COLUMN,
    TITLE_COLUMN,
    ANNOTATION_COLUMN,
}


@dataclass(slots=True)
class SplitBooks:
    annotated: pd.DataFrame
    unannotated: pd.DataFrame


def load_excel(path: str | Path, sheet_name: str | int = 0) -> pd.DataFrame:
    """Load the source spreadsheet and retain the original source row number.

    XLSX/XLSM and CSV files are supported. Fully empty rows are removed.
    ``Quellzeile`` points to the row number in the original file (header is row
    1). If an input file already contains ``Quellzeile``, it is preserved.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        frame = pd.read_csv(path, sep=None, engine="python")
    elif suffix in {".xlsx", ".xlsm"}:
        frame = pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
    else:
        raise ValueError(
            "Nicht unterstütztes Eingabeformat. Unterstützt werden: .csv, .xlsx, .xlsm"
        )

    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Fehlende Pflichtspalten: {missing_text}")

    # pandas index 0 corresponds to source row 2 because row 1 is the header.
    if SOURCE_ROW_COLUMN not in frame.columns:
        frame.insert(0, SOURCE_ROW_COLUMN, frame.index + 2)

    source_columns = [column for column in frame.columns if column != SOURCE_ROW_COLUMN]
    frame = frame.dropna(how="all", subset=source_columns).copy()

    return frame


def is_annotated(value: object) -> bool:
    """A row is annotated when the ThULB annotation cell is non-empty.

    This intentionally does not interpret the annotation. Both ``x`` and a
    value such as ``einmal verfügbar`` count as annotated. Positive/negative
    interpretation belongs to the later evaluation step.
    """
    if pd.isna(value):
        return False
    return bool(str(value).strip())


def split_by_annotation(
    frame: pd.DataFrame,
    annotation_column: str = ANNOTATION_COLUMN,
) -> SplitBooks:
    if annotation_column not in frame.columns:
        raise ValueError(f"Annotationsspalte nicht gefunden: {annotation_column}")

    mask = frame[annotation_column].map(is_annotated)
    return SplitBooks(
        annotated=frame.loc[mask].copy(),
        unannotated=frame.loc[~mask].copy(),
    )


def select_source_rows(
    frame: pd.DataFrame,
    source_rows: Iterable[int] | None,
) -> pd.DataFrame:
    """Optionally select rows by their original source row number.

    ``None`` means: keep all rows.
    """
    if source_rows is None:
        return frame.copy()

    selected = set(source_rows)
    return frame.loc[frame[SOURCE_ROW_COLUMN].isin(selected)].copy()


def export_split(
    split: SplitBooks,
    output_dir: str | Path,
    *,
    annotated_filename: str = "annotiert.csv",
    unannotated_filename: str = "unannotiert.csv",
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    annotated_path = output_dir / annotated_filename
    unannotated_path = output_dir / unannotated_filename

    split.annotated.to_csv(annotated_path, index=False)
    split.unannotated.to_csv(unannotated_path, index=False)

    return annotated_path, unannotated_path


def to_books(frame: pd.DataFrame) -> list[Book]:
    """Convert extracted rows to the minimal domain model for later matching."""
    books: list[Book] = []

    for _, row in frame.iterrows():
        books.append(
            Book(
                source_row=int(row[SOURCE_ROW_COLUMN]),
                author=_optional_text(row[AUTHOR_COLUMN]),
                title=_optional_text(row[TITLE_COLUMN]),
                year_raw=_optional_scalar(row[YEAR_COLUMN]),
                annotation_raw=_optional_text(row[ANNOTATION_COLUMN]),
            )
        )

    return books


def _optional_text(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _optional_scalar(value: object) -> int | float | str | None:
    if pd.isna(value):
        return None
    return value
