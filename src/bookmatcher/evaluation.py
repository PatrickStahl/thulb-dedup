from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


SOURCE_ROW_COLUMN = "Quellzeile"
ANNOTATION_COLUMN = "Anzahl des Exemplares in Thulb"
MATCH_STATUS_COLUMN = "match_status"


def evaluate(
    input_path: str | Path,
) -> dict[str, float | int]:
    """
    Evaluate matching results against existing ThULB annotations.

    Ground truth:
        empty annotation -> ignored
        "x"              -> not available
        everything else  -> available

    Prediction:
        any match_status == "ok" for a source row -> available
        otherwise                               -> not available
    """

    input_path = Path(input_path)

    rows = _read_csv(input_path)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row in rows:
        source_row = row.get(SOURCE_ROW_COLUMN, "").strip()

        if not source_row:
            continue

        grouped[source_row].append(row)

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for source_row, group in grouped.items():
        annotation = _get_annotation(group)

        ground_truth = _parse_ground_truth(annotation)

        if ground_truth is None:
            continue

        prediction = any(
            row.get(MATCH_STATUS_COLUMN, "").strip().lower() == "ok"
            for row in group
        )

        if ground_truth and prediction:
            tp += 1

        elif not ground_truth and prediction:
            fp += 1

        elif not ground_truth and not prediction:
            tn += 1

        elif ground_truth and not prediction:
            fn += 1

    total = tp + fp + tn + fn

    precision = _safe_divide(
        tp,
        tp + fp,
    )

    recall = _safe_divide(
        tp,
        tp + fn,
    )

    accuracy = _safe_divide(
        tp + tn,
        total,
    )

    return {
        "total": total,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
    }


def _read_csv(
    path: Path,
) -> list[dict[str, str]]:
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

        required = {
            SOURCE_ROW_COLUMN,
            ANNOTATION_COLUMN,
            MATCH_STATUS_COLUMN,
        }

        missing = required - set(reader.fieldnames)

        if missing:
            raise ValueError(
                "Missing required columns: "
                + ", ".join(sorted(missing))
            )

        return list(reader)


def _get_annotation(
    rows: list[dict[str, str]],
) -> str:
    """
    Get the annotation for one source record.

    All candidate rows originate from the same input row,
    so the annotation should be identical.
    """

    for row in rows:
        value = row.get(
            ANNOTATION_COLUMN,
            "",
        ).strip()

        if value:
            return value

    return ""


def _parse_ground_truth(
    annotation: str,
) -> bool | None:
    """
    Convert the existing annotation to a binary label.

    Returns:
        True  -> available
        False -> unavailable
        None  -> no ground truth
    """

    annotation = annotation.strip()

    if not annotation:
        return None

    if annotation.lower() == "x":
        return False

    return True


def _safe_divide(
    numerator: int,
    denominator: int,
) -> float:
    if denominator == 0:
        return 0.0

    return numerator / denominator


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate book matching results against "
            "existing ThULB annotations."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Matching output CSV.",
    )

    args = parser.parse_args()

    result = evaluate(args.input)

    print(f"Evaluated: {result['total']}")
    print()
    print(
        f"TP: {result['tp']}  "
        f"FP: {result['fp']}  "
        f"TN: {result['tn']}  "
        f"FN: {result['fn']}"
    )
    print()
    print(
        f"Precision: {result['precision']:.4f}"
    )
    print(
        f"Recall:    {result['recall']:.4f}"
    )
    print(
        f"Accuracy:  {result['accuracy']:.4f}"
    )


if __name__ == "__main__":
    main()