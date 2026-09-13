import xml.etree.ElementTree as ET

from bookmatcher.k10plus import K10PlusClient, _parse_pica_record


def test_build_query_adds_volume_as_tmb_index():
    query = K10PlusClient._build_query(
        title="Deutsche Wortforschung in europäischen Bezügen",
        author="Schmitt",
        volume="3",
    )

    assert query == (
        "pica.tit=Deutsche Wortforschung in europäischen Bezügen "
        "AND pica.per=Schmitt "
        "AND pica.tmb=3"
    )


def test_parse_pica_record_falls_back_to_multipart_title_and_volume():
    record = ET.fromstring(
        """
        <record xmlns="info:srw/schema/5/picaXML-v1.0">
          <datafield tag="003@">
            <subfield code="0">03040472X</subfield>
          </datafield>
          <datafield tag="011@">
            <subfield code="a">1963</subfield>
          </datafield>
          <datafield tag="036C">
            <subfield code="a">Deutsche Wortforschung in europäischen Bezügen</subfield>
            <subfield code="d">Untersuchungen zum Deutschen Wortatlas</subfield>
            <subfield code="l">Bd. III</subfield>
          </datafield>
        </record>
        """
    )

    result = _parse_pica_record(record)

    assert result.ppn == "03040472X"
    assert result.title == (
        "Deutsche Wortforschung in europäischen Bezügen "
        ": Untersuchungen zum Deutschen Wortatlas"
    )
    assert result.year == 1963
    assert result.volume == "3"
