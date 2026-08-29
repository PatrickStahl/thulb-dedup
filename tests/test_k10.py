from bookmatcher.k10plus import K10PlusClient
from bookmatcher.models import Book
from bookmatcher.ranking import rank_candidates


book = Book(
    source_row=2,
    author="Admoni, Vladimir",
    title="Der deutsche Sprachbau",
    year_raw=1966,
)

client = K10PlusClient()

records = client.search(
    title=book.title,
    author=book.author,
    limit=10,
)

ranked = rank_candidates(
    book,
    records,
    top_k=3,
)

for candidate in ranked:
    print(
        candidate.year_distance,
        candidate.record.ppn,
        candidate.record.year,
        candidate.record.title,
    )