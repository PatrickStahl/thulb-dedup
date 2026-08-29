import pytest

from bookmatcher.main import parse_row_selection


def test_parse_row_selection_empty_means_all():
    assert parse_row_selection("") is None


def test_parse_row_selection_supports_ranges_and_single_rows():
    assert parse_row_selection("2-4, 8, 10-11") == {2, 3, 4, 8, 10, 11}


def test_parse_row_selection_rejects_reverse_range():
    with pytest.raises(ValueError):
        parse_row_selection("10-2")
