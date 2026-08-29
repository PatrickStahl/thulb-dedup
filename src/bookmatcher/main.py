from __future__ import annotations

import argparse
from pathlib import Path

from .excel import (
    SplitBooks,
    export_split,
    load_excel,
    select_source_rows,
    split_by_annotation,
)


def parse_row_selection(value: str) -> set[int] | None:
    """Parse e.g. ``2-20,25,40-45``. Empty input means all rows."""
    value = value.strip()
    if not value:
        return None

    rows: set[int] = set()

    for part in value.split(","):
        part = part.strip()
        if not part:
            continue

        if "-" in part:
            start_text, end_text = part.split("-", maxsplit=1)
            start = int(start_text.strip())
            end = int(end_text.strip())
            if start > end:
                raise ValueError(f"Ungültiger Bereich: {part}")
            rows.update(range(start, end + 1))
        else:
            rows.add(int(part))

    return rows


def ask_for_manual_selection(split: SplitBooks) -> SplitBooks:
    print()
    answer = input("Manuelle Zeilenauswahl verwenden? [y/N]: ").strip().lower()
    if answer not in {"y", "yes", "j", "ja"}:
        return split

    print("Angabe über ursprüngliche Eingabe-Zeilennummern, z. B. 2-20,25,40-45.")
    print("Leere Eingabe bedeutet jeweils: alle Zeilen dieser Gruppe.")

    annotated_rows = parse_row_selection(
        input("Annotierte Zeilen auswählen [alle]: ")
    )
    unannotated_rows = parse_row_selection(
        input("Unannotierte Zeilen auswählen [alle]: ")
    )

    _print_ignored_rows("annotiert", split.annotated, annotated_rows)
    _print_ignored_rows("unannotiert", split.unannotated, unannotated_rows)

    return SplitBooks(
        annotated=select_source_rows(split.annotated, annotated_rows),
        unannotated=select_source_rows(split.unannotated, unannotated_rows),
    )


def _print_ignored_rows(label: str, frame, selected_rows: set[int] | None) -> None:
    if selected_rows is None:
        return

    available_rows = set(frame["Quellzeile"].astype(int))
    ignored = sorted(selected_rows - available_rows)
    if ignored:
        preview = ", ".join(map(str, ignored[:10]))
        suffix = " ..." if len(ignored) > 10 else ""
        print(
            f"Hinweis: {len(ignored)} angegebene Zeile(n) gehören nicht zur "
            f"Gruppe '{label}' und werden ignoriert: {preview}{suffix}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Teilt die Buchliste anhand der ThULB-Annotationsspalte auf."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Pfad zur Eingabe-Datei (.csv, .xlsx, .xlsm)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Ausgabeordner (Default: output)",
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Keine interaktive Auswahl; immer alle Datensätze exportieren.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    frame = load_excel(args.input)
    split = split_by_annotation(frame)

    print(f"Datensätze insgesamt: {len(frame)}")
    print(f"Annotiert:           {len(split.annotated)}")
    print(f"Unannotiert:         {len(split.unannotated)}")

    if not args.no_prompt:
        split = ask_for_manual_selection(split)

    annotated_path, unannotated_path = export_split(split, args.output_dir)

    print()
    print(f"Export annotiert:   {len(split.annotated):>5} -> {annotated_path}")
    print(f"Export unannotiert: {len(split.unannotated):>5} -> {unannotated_path}")


if __name__ == "__main__":
    main()
