# ThULB Book Matcher

## Ziel

Dieses Projekt gleicht einen lokalen Buchbestand mit dem K10plus-Katalogbestand der Thüringer Universitäts- und Landesbibliothek (ThULB) ab. Das Verfahren ist bewusst heuristisch und dient als **Kandidatengenerator für eine anschließende manuelle Prüfung**: Gefundene Treffer sind sehr zuverlässig, nicht gefundene Titel können aber trotzdem im Bestand vorhanden sein.

## Erwartete Datenstruktur

Die Eingabedatei kann als `.csv`, `.xlsx` oder `.xlsm` vorliegen. Die erste Zeile muss die Spaltennamen enthalten; vollständig leere Zeilen werden ignoriert.

Pflichtspalten:

```text
Autor/Herausgeber
Erscheinungsjahr
Titel (Auflage)
Anzahl des Exemplares in Thulb
```

Falls keine Spalte `Quellzeile` vorhanden ist, wird sie beim Einlesen automatisch ergänzt. Sie verweist auf die ursprüngliche Zeilennummer der Eingabedatei und wird später verwendet, um Kandidaten wieder eindeutig dem Ausgangsdatensatz zuzuordnen.

## Usage

Empfohlen ist die Ausführung mit `uv`.

```bash
uv sync
```

Eingabedatei nach vorhandener ThULB-Annotation aufteilen:

```bash
uv run bookmatcher data/buecher.xlsx
```

Ohne interaktive Zeilenauswahl:

```bash
uv run bookmatcher data/buecher.xlsx --no-prompt
```

Ausgabeordner festlegen:

```bash
uv run bookmatcher data/buecher.xlsx --output-dir output
```

K10plus-Matching auf einer exportierten CSV ausführen:

```bash
uv run python -m bookmatcher.batch output/annotiert.csv output/annotiert_matches.csv
```

Wichtige Matching-Optionen:

```bash
uv run python -m bookmatcher.batch output/annotiert.csv output/annotiert_matches.csv --top-k 3 --search-limit 10 --delay 0.1
```

Evaluation gegen vorhandene Annotationen:

```bash
uv run python -m bookmatcher.evaluation output/annotiert_matches.csv
```

Tests ausführen:

```bash
uv run pytest
```

## `bookmatcher`

### Aufteilen der Eingabedaten

Der CLI-Befehl `bookmatcher` liest die Eingabedatei ein, prüft die Pflichtspalten und teilt die Datensätze anhand der Spalte `Anzahl des Exemplares in Thulb` in zwei CSV-Dateien auf:

```text
output/annotiert.csv
output/unannotiert.csv
```

Eine Zeile gilt als annotiert, sobald die Annotationsspalte nicht leer ist. Dabei wird noch nicht interpretiert, ob die Annotation einen Treffer oder keinen Treffer bedeutet.

### Kandidatensuche

Für den normalen Workflow werden nur Autor und Titel verwendet. Der Autor wird für die Anfrage auf den Nachnamen reduziert, weil Vornamen in historischen und bibliographischen Daten unterschiedlich geschrieben oder transliteriert sein können.

```text
Admoni, Vladimir
→ Admoni
```

Die K10plus-Anfrage entspricht konzeptionell:

```text
pica.tit=<Titel> AND pica.per=<Nachname>
```

Da Titel und Name bereits weit gefasst sind, wird kein Fallback auf reine Autor- oder Titel-Suchen durchgeführt.

### Titelnormalisierung

Vor der Kataloganfrage wird der Titel leicht normalisiert. Entfernt werden nur klar erkennbare bibliographische Zusätze wie Auflagen-, Band- oder ähnliche Angaben; der eigentliche Titel wird nicht fuzzy verändert.

```text
Althochdeutsches Lesebuch (11. Aufl.)
→ Althochdeutsches Lesebuch

Einführung in die Sprachwissenschaft Band 1
→ Einführung in die Sprachwissenschaft

Deutsche Grammatik 3. Aufl.
→ Deutsche Grammatik
```

### Ranking

Die Katalogschnittstelle liefert Kandidaten zu Titel und Autor. Anschließend wird die Distanz zwischen lokalem Erscheinungsjahr und Katalogjahr berechnet; Kandidaten mit der kleinsten Jahresdifferenz werden zuerst ausgegeben. Standardmäßig werden die besten drei Kandidaten exportiert (`top_k=3`).

### Output

Der Matching-Output enthält die ursprünglichen Spalten und zusätzliche Ergebnisfelder:

```text
match_status
candidate_count
candidate_rank
candidate_ppn
candidate_title
candidate_authors
candidate_year
year_distance
error
```

`match_status` kann folgende Werte haben:

```text
ok             mindestens ein Kandidat wurde gefunden
no_results     keine Kandidaten für Titel und Autor
missing_input  Titel oder Autor fehlt
error          technische Anfrage fehlgeschlagen
```

## Evaluation

Für die Entwicklung standen manuell annotierte Datensätze zur Verfügung. Die bestehenden Annotationen wurden so interpretiert:

```text
"x"                               → nicht vorhanden
jede andere nichtleere Annotation → vorhanden
leere Annotation                   → unbekannt / nicht für Evaluation verwendet
```

Nach Einführung der Titelnormalisierung ergaben sich:

```text
TP: 197
FP:   5
TN: 122
FN:  43
```

Daraus:

```text
Precision: 0.9752
Recall:    0.8208
Accuracy:  0.8692
```

Die hohe Precision bedeutet, dass gefundene Treffer sehr häufig mit der bisherigen manuellen Annotation übereinstimmen. Bei den wenigen False Positives ist anzunehmen, dass ein Teil auf nicht gefundene Treffer in der ursprünglichen Annotation zurückgeht; diese Fälle können bei Bedarf nachevaluiert werden. Der geringere Recall zeigt, dass die konservative Suchstrategie vorhandene Bücher teilweise nicht findet.

## Hinweise für die manuelle Prüfung

TL;DR: Der erste Kandidat ist ein Vorschlag, keine Entscheidung. `year_distance = 0` ist ein starkes Signal, ersetzt aber nicht den Vergleich von Autor, Titel und Erscheinungsjahr. Unterschiedliche Vornamen, Zeichensetzung, Untertitel oder transliterierte Schreibweisen sind in bibliographischen Daten normal und sollten nicht allein zum Verwerfen führen. Wichtig ist außerdem die Unterscheidung zwischen gleichem Werk und gleicher Ausgabe, besonders bei häufig aufgelegten Titeln.
