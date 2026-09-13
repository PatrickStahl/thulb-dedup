from __future__ import annotations

import argparse
from pathlib import Path

from .excel import reconstruct_original_output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Rekonstruiert die ursprüngliche Buchlisten-Struktur "
            "und ergänzt Trefferanzahl sowie PPN."
        )
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Ursprüngliche Eingabe-Datei (.csv, .xlsx, .xlsm)",
    )
    parser.add_argument(
        "matches",
        type=Path,
        help="Matching-Ergebnis, z. B. output/unannotiert_matches.csv",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Ausgabe-Datei (.csv oder .xlsx)",
    )
    parser.add_argument(
        "--sheet",
        default=0,
        help="Excel-Sheetname oder -Index der Eingabe-Datei (Default: 0)",
    )
    return parser


def _parse_sheet(value: str) -> str | int:
    try:
        return int(value)
    except ValueError:
        return value


def main() -> None:
    args = build_parser().parse_args()

    output_path = reconstruct_original_output(
        args.input,
        args.matches,
        args.output,
        sheet_name=_parse_sheet(str(args.sheet)),
    )

    print(f"Rekonstruierte Buchliste exportiert: {output_path}")


if __name__ == "__main__":
    main()
