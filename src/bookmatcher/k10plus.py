from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import requests

from bookmatcher.normalization import (
    extract_volume,
    normalize_author_for_query,
    normalize_title_for_query,
)

from .models import CatalogRecord


DEFAULT_BASE_URL = "https://sru.k10plus.de/opac-de-27"


class K10PlusError(RuntimeError):
    """Raised when communication with the K10plus SRU endpoint fails."""


class K10PlusClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 20.0,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "bookmatcher/0.1",
            }
        )

    def search(
        self,
        title: str | None = None,
        author: str | None = None,
        volume: str | None = None,
        limit: int = 10,
    ) -> list[CatalogRecord]:
        """
        Search the ThULB/K10plus catalog.

        At least one of title or author must be provided.

        The normal batch workflow should provide both fields.
        Supplying only one field is mainly useful for manual testing.
        """

        title = (
            normalize_title_for_query(title)
            if title
            else None
        )

        author = (
            normalize_author_for_query(author)
            if author
            else None
        )

        volume = extract_volume(volume) if volume else None

        if not title and not author:
            raise ValueError(
                "At least one of title or author must be provided"
            )

        if not 1 <= limit <= 100:
            raise ValueError(
                "limit must be between 1 and 100"
            )

        query = self._build_query(
            title=title,
            author=author,
            volume=volume,
        )

        params = {
            "version": "1.1",
            "operation": "searchRetrieve",
            "query": query,
            "maximumRecords": str(limit),
            "startRecord": "1",
            "recordSchema": "picaxml",
        }

        try:
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise K10PlusError(
                f"K10plus request failed: {exc}"
            ) from exc

        records = _parse_response(response.content)
        if volume is not None:
            records = [
                record
                for record in records
                if record.volume == volume
            ]

        return records

    @staticmethod
    def _build_query(
        title: str | None,
        author: str | None,
        volume: str | None = None,
    ) -> str:
        query_parts: list[str] = []

        if title:
            title_term = _escape_cql_term(title)

            query_parts.append(
                f"pica.tit={title_term}"
            )

        if author:
            author_term = _escape_cql_term(author)

            query_parts.append(
                f"pica.per={author_term}"
            )

        if volume:
            volume_term = _escape_cql_term(volume)

            query_parts.append(
                f"pica.tmb={volume_term}"
            )

        if not query_parts:
            raise ValueError(
                "At least one search field is required"
            )

        return " AND ".join(query_parts)

def _number_of_records(root: ET.Element) -> int:
    for element in root.iter():
        if _local_name(element.tag) == "numberOfRecords":
            if element.text:
                return int(element.text)

    return 0


def _escape_cql_term(value: str) -> str:
    """
    Escape characters that may interfere with the CQL query.

    Whitespace is preserved because pica.tit and pica.per are search
    indexes that can process multiple words.
    """

    value = value.replace("\\", "\\\\")

    for char in (
        ".",
        "(",
        ")",
        "<",
        ">",
        "/",
        '"',
    ):
        value = value.replace(char, f"\\{char}")

    # Prevent words in titles such as "and", "or" or "not" from being
    # interpreted as CQL boolean operators.
    value = re.sub(
        r"\b(and|or|not)\b",
        lambda match: "\\" + match.group(0),
        value,
        flags=re.IGNORECASE,
    )

    return value


def _parse_response(content: bytes) -> list[CatalogRecord]:
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise K10PlusError(
            "K10plus returned invalid XML"
        ) from exc

    diagnostic = _find_diagnostic(root)
    if diagnostic is not None:
        raise K10PlusError(
            f"K10plus SRU diagnostic: {diagnostic}"
        )

    number_of_records = _number_of_records(root)

    print(
        f"K10plus reports {number_of_records} matching records."
    )

    records: list[CatalogRecord] = []

    for element in root.iter():
        if _local_name(element.tag) != "recordData":
            continue

        pica_record = _find_pica_record(element)

        if pica_record is None:
            continue

        records.append(
            _parse_pica_record(pica_record)
        )

    print(
        f"Parsed {len(records)} PICA records."
    )

    return records

def _find_pica_record(
    record_data: ET.Element,
) -> ET.Element | None:
    for child in record_data:
        if _local_name(child.tag) == "record":
            return child

    return None


def _parse_pica_record(
    record: ET.Element,
) -> CatalogRecord:
    ppn = _first_subfield(
        record,
        field_tag="003@",
        code="0",
    )

    title = _extract_title(record)

    year_raw = _first_subfield(
        record,
        field_tag="011@",
        code="a",
    )

    authors = _extract_authors(record)
    volume = _extract_volume(record)

    return CatalogRecord(
        ppn=ppn,
        title=title,
        authors=authors,
        year=_parse_year(year_raw),
        raw_xml=ET.tostring(
            record,
            encoding="unicode",
        ),
        volume=volume,
    )


def _extract_title(record: ET.Element) -> str | None:
    main_title = _first_subfield(
        record,
        field_tag="021A",
        code="a",
    )

    if main_title is not None:
        return _clean_pica_text(main_title)

    multipart_title = _first_subfield(
        record,
        field_tag="036C",
        code="a",
    )
    subtitle = _first_subfield(
        record,
        field_tag="036C",
        code="d",
    )

    title_parts = [
        _clean_pica_text(part)
        for part in (multipart_title, subtitle)
        if part
    ]

    if not title_parts:
        return None

    return " : ".join(title_parts)


def _extract_volume(record: ET.Element) -> str | None:
    for field_tag in ("036C", "036D"):
        raw_volume = _first_subfield(
            record,
            field_tag=field_tag,
            code="l",
        )
        volume = extract_volume(raw_volume)
        if volume is not None:
            return volume

    return None


def _extract_authors(
    record: ET.Element,
) -> tuple[str, ...]:
    authors: list[str] = []

    for field in record.iter():
        if _local_name(field.tag) != "datafield":
            continue

        field_tag = field.attrib.get("tag", "")

        # Person fields in PICA+ use the 028* range.
        if not field_tag.startswith("028"):
            continue

        personal_name = _subfield_value(
            field,
            code="P",
        )

        surname = _subfield_value(
            field,
            code="a",
        )

        first_name = _subfield_value(
            field,
            code="d",
        )

        if personal_name:
            author = personal_name

        elif surname and first_name:
            author = f"{surname}, {first_name}"

        elif surname:
            author = surname

        else:
            continue

        author = _clean_pica_text(author)

        if author and author not in authors:
            authors.append(author)

    return tuple(authors)


def _first_subfield(
    record: ET.Element,
    field_tag: str,
    code: str,
) -> str | None:
    for field in record.iter():
        if _local_name(field.tag) != "datafield":
            continue

        if field.attrib.get("tag") != field_tag:
            continue

        value = _subfield_value(
            field,
            code=code,
        )

        if value is not None:
            return value

    return None


def _subfield_value(
    field: ET.Element,
    code: str,
) -> str | None:
    for subfield in field:
        if _local_name(subfield.tag) != "subfield":
            continue

        if subfield.attrib.get("code") != code:
            continue

        if subfield.text:
            return subfield.text.strip()

    return None


def _parse_year(
    value: str | None,
) -> int | None:
    if not value:
        return None

    match = re.search(r"\d{4}", value)

    if match is None:
        return None

    return int(match.group(0))


def _clean_pica_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    # PICA uses @ as a marker for non-sorting title components.
    value = value.replace("@", "")

    return " ".join(value.split())


def _find_diagnostic(
    root: ET.Element,
) -> str | None:
    for element in root.iter():
        if _local_name(element.tag) != "diagnostic":
            continue

        for child in element.iter():
            if (
                _local_name(child.tag) == "message"
                and child.text
            ):
                return child.text.strip()

        return "unknown SRU error"

    return None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1]
