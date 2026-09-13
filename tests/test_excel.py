import pandas as pd
from openpyxl import load_workbook

from bookmatcher.excel import (
    ANNOTATION_COLUMN,
    AUTHOR_COLUMN,
    TITLE_COLUMN,
    YEAR_COLUMN,
    PPN_COLUMN,
    SOURCE_ROW_COLUMN,
    SplitBooks,
    append_match_results_to_original,
    export_split,
    load_excel,
    reconstruct_original_output,
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


def test_append_match_results_recreates_original_columns_with_ppn():
    source = pd.DataFrame(
        {
            SOURCE_ROW_COLUMN: [2, 3, 4],
            AUTHOR_COLUMN: ["Ada", "Grace", "Edsger"],
            YEAR_COLUMN: [1843, 1952, 1968],
            TITLE_COLUMN: ["Notes", "Compiler", "Letters"],
            ANNOTATION_COLUMN: ["", "", "already annotated"],
            "Ort": ["London", "New York", "Nuenen"],
        }
    )
    matches = pd.DataFrame(
        {
            SOURCE_ROW_COLUMN: [2, 2, 3],
            "candidate_ppn": ["PPN-1", "PPN-2", ""],
        }
    )

    result = append_match_results_to_original(source, matches)

    assert list(result.columns) == [
        AUTHOR_COLUMN,
        YEAR_COLUMN,
        TITLE_COLUMN,
        ANNOTATION_COLUMN,
        "Ort",
        PPN_COLUMN,
    ]
    assert result[AUTHOR_COLUMN].tolist() == ["Ada", "Grace", "Edsger"]
    assert result[ANNOTATION_COLUMN].tolist() == [2, 0, "already annotated"]
    assert result[PPN_COLUMN].tolist() == ["PPN-1, PPN-2", "", ""]


def test_reconstruct_original_output_writes_csv_and_xlsx(tmp_path):
    input_path = tmp_path / "books.csv"
    input_path.write_text(
        "\n".join(
            [
                f"{AUTHOR_COLUMN},{YEAR_COLUMN},{TITLE_COLUMN},{ANNOTATION_COLUMN}",
                "Ada,1843,Notes,",
            ]
        ),
        encoding="utf-8",
    )
    matches_path = tmp_path / "matches.csv"
    matches_path.write_text(
        "\n".join(
            [
                f"{SOURCE_ROW_COLUMN},candidate_ppn",
                "2,PPN-1",
            ]
        ),
        encoding="utf-8",
    )
    csv_output_path = tmp_path / "out.csv"
    xlsx_output_path = tmp_path / "out.xlsx"

    reconstruct_original_output(input_path, matches_path, csv_output_path)
    reconstruct_original_output(input_path, matches_path, xlsx_output_path)

    csv_result = pd.read_csv(csv_output_path)
    xlsx_result = pd.read_excel(xlsx_output_path, engine="openpyxl")

    assert csv_result[PPN_COLUMN].tolist() == ["PPN-1"]
    assert xlsx_result[PPN_COLUMN].tolist() == ["PPN-1"]

    workbook = load_workbook(xlsx_output_path)
    worksheet = workbook.active

    assert worksheet.auto_filter.ref == "A1:E2"
    assert worksheet.freeze_panes == "A2"
    assert worksheet["A1"].fill.fgColor.rgb == "00000000"
    assert worksheet["A1"].font.color.rgb == "00FFFFFF"
    assert worksheet["A2"].fill.fgColor.rgb == "00D9D9D9"
    assert worksheet["B2"].fill.fill_type is None
