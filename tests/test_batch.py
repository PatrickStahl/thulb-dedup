import pandas as pd

from bookmatcher.batch import run_batch
from bookmatcher.models import CatalogRecord
from bookmatcher.normalization import SEARCH_TITLE_COLUMN, VOLUME_COLUMN


class FakeClient:
    def __init__(self) -> None:
        self.calls = []

    def search(
        self,
        *,
        title: str,
        author: str,
        volume: str | None,
        limit: int,
    ) -> list[CatalogRecord]:
        self.calls.append(
            {
                "title": title,
                "author": author,
                "volume": volume,
                "limit": limit,
            }
        )
        return [
            CatalogRecord(
                ppn="PPN-1",
                title="Clean Catalog Title",
                authors=("Ada",),
                year=1843,
                raw_xml="",
                volume=volume,
            )
        ]


def test_run_batch_prefers_cleanup_columns_for_catalog_query(tmp_path):
    input_path = tmp_path / "input.csv"
    input_path.write_text(
        "\n".join(
            [
                "Quellzeile,Autor/Herausgeber,Erscheinungsjahr,Titel (Auflage),Such-Titel,Band",
                '2,"Ada, Lovelace",1843,"Raw Title Band III","Clean Title",3',
            ]
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "matches.csv"
    client = FakeClient()

    run_batch(
        input_path,
        output_path,
        client=client,
        top_k=1,
        search_limit=1,
        delay_seconds=0,
    )

    assert client.calls == [
        {
            "title": "Clean Title",
            "author": "Ada, Lovelace",
            "volume": "3",
            "limit": 1,
        }
    ]

    result = pd.read_csv(output_path)

    assert result[SEARCH_TITLE_COLUMN].tolist() == ["Clean Title"]
    assert result[VOLUME_COLUMN].tolist() == [3]
    assert result["candidate_ppn"].tolist() == ["PPN-1"]
