from bookmatcher.k10plus import K10PlusClient


client = K10PlusClient()

records = client.search(
    title="Der deutsche Sprachbau",
    author="Admoni, Vladimir",
    limit=10,
)

for record in records:
    print(
        record.ppn,
        record.year,
        record.title,
        record.authors,
    )

if not records:
    print("No records found.")