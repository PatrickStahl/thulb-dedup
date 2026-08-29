import pandas as pd

from bookmatcher.excel import (
    ANNOTATION_COLUMN,
    AUTHOR_COLUMN,
    TITLE_COLUMN,
    YEAR_COLUMN,
    SOURCE_ROW_COLUMN,
    SplitBooks,
    export_split,
    load_excel,
    select_source_rows,
    split_by_annotation,
)


def test_split_by_annotation_treats_every_non_empty_value_as_annotated():
    frame = pd.DataFrame(
        {
            SOURCE_ROW_COLUMN: [2, 3, 4, 5],
            ANNOTATION_COLUMN: [None, "", "x", "einmal verfügbar"],
        }
    )

    split = split_by_annotation(frame)

    assert split.annotated[SOURCE_ROW_COLUMN].tolist() == [4, 5]
    assert split.unannotated[SOURCE_ROW_COLUMN].tolist() == [2, 3]


def test_select_source_rows_none_means_all():
    frame = pd.DataFrame({SOURCE_ROW_COLUMN: [2, 10, 20]})

    result = select_source_rows(frame, None)

    assert result[SOURCE_ROW_COLUMN].tolist() == [2, 10, 20]


def test_select_source_rows_filters_original_excel_rows():
    frame = pd.DataFrame({SOURCE_ROW_COLUMN: [2, 10, 20]})

    result = select_source_rows(frame, {10, 20})

    assert result[SOURCE_ROW_COLUMN].tolist() == [10, 20]


def test_load_excel_supports_csv_input(tmp_path):
    csv_path = tmp_path / "books.csv"
    csv_path.write_text(
        "\n".join(
            [
                f"{AUTHOR_COLUMN},{YEAR_COLUMN},{TITLE_COLUMN},{ANNOTATION_COLUMN}",
                "Ada,1843,Notes,x",
                "Grace,1952,Compiler,",
            ]
        ),
        encoding="utf-8",
    )

    result = load_excel(csv_path)

    assert result[SOURCE_ROW_COLUMN].tolist() == [2, 3]
    assert result[AUTHOR_COLUMN].tolist() == ["Ada", "Grace"]


def test_load_excel_preserves_existing_source_row_from_csv(tmp_path):
    csv_path = tmp_path / "books.csv"
    csv_path.write_text(
        "\n".join(
            [
                f"{SOURCE_ROW_COLUMN},{AUTHOR_COLUMN},{YEAR_COLUMN},{TITLE_COLUMN},{ANNOTATION_COLUMN}",
                "10,Ada,1843,Notes,x",
            ]
        ),
        encoding="utf-8",
    )

    result = load_excel(csv_path)

    assert result[SOURCE_ROW_COLUMN].tolist() == [10]


def test_export_split_writes_csv_files(tmp_path):
    split = SplitBooks(
        annotated=pd.DataFrame({SOURCE_ROW_COLUMN: [2], AUTHOR_COLUMN: ["Ada"]}),
        unannotated=pd.DataFrame({SOURCE_ROW_COLUMN: [3], AUTHOR_COLUMN: ["Grace"]}),
    )

    annotated_path, unannotated_path = export_split(split, tmp_path)

    assert annotated_path.name == "annotiert.csv"
    assert unannotated_path.name == "unannotiert.csv"
    assert pd.read_csv(annotated_path)[AUTHOR_COLUMN].tolist() == ["Ada"]
    assert pd.read_csv(unannotated_path)[AUTHOR_COLUMN].tolist() == ["Grace"]
