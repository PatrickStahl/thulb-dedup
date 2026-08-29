from bookmatcher.k10plus import K10PlusClient


client = K10PlusClient()

records = client.search(
    author="Admoni, Vladimir",
    title="Die thüringisch-sächsische Kanzlersprache bis 1325",
    limit=10,
)

# Full sample entry
# records = client.search(
#     author="Admoni, Vladimir",
#     title="Die thüringisch-sächsische Kanzlersprache bis 1325",
#     limit=10,
# )

for record in records:
    print(
        record.ppn,
        record.year,
        record.title,
        record.authors,
    )