# ThULB Book Matcher

## Ziel

Dieses Projekt gleicht einen lokalen Buchbestand mit dem K10plus-Katalogbestand der Thüringer Universitäts- und Landesbibliothek (ThULB) ab. Das Verfahren ist bewusst heuristisch und dient als **Kandidatengenerator für eine anschließende manuelle Prüfung**: Gefundene Treffer sind sehr zuverlässig, nicht gefundene Titel können aber trotzdem im Bestand vorhanden sein.

## Inhalt

- [Erwartete Datenstruktur](#erwartete-datenstruktur)
- [Schnellstart unter Windows](#schnellstart-unter-windows)
- [Schnellstart unter Linux](#schnellstart-unter-linux)
- [Automatisches Setup](#automatisches-setup)
- [`bookmatcher`](#bookmatcher)
- [Evaluation](#evaluation)
- [Hinweise für die manuelle Prüfung](#hinweise-für-die-manuelle-prüfung)

## Erwartete Datenstruktur

Die Eingabedatei kann als `.csv`, `.xlsx` oder `.xlsm` vorliegen. Die erste Zeile muss die Spaltennamen enthalten; vollständig leere Zeilen werden ignoriert.

Pflichtspalten:

```text
Autor/Herausgeber
Erscheinungsjahr
Titel (Auflage)
Anzahl des Exemplares in Thulb
```

Die Spalte `Anzahl des Exemplares in Thulb` muss auch dann vorhanden sein, wenn noch keine manuelle ThULB-Prüfung existiert. In diesem Fall bleibt sie einfach leer; die Datensätze landen dann beim Aufteilen in `output/unannotiert.csv`.

Falls keine Spalte `Quellzeile` vorhanden ist, wird sie beim Einlesen automatisch ergänzt. Sie verweist auf die ursprüngliche Zeilennummer der Eingabedatei und wird später verwendet, um Kandidaten wieder eindeutig dem Ausgangsdatensatz zuzuordnen.

## Schnellstart unter Windows

Die folgenden Schritte gehen davon aus, dass die Buchliste im Projektordner unter `data\Buchliste.xlsx` liegt. Wenn die Datei anders heißt, muss nur dieser Dateiname im ersten Arbeitsbefehl angepasst werden.

1. Den Projektordner im Windows-Explorer öffnen.
2. In die Adresszeile des Explorers `powershell` eingeben und Enter drücken.
3. Einmalig das Setup starten:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1
```

4. Danach dieses PowerShell-Fenster schließen.
5. Den Projektordner wieder im Windows-Explorer öffnen, in die Adresszeile `powershell` eingeben und Enter drücken.

Danach besteht der normale Arbeitsablauf aus zwei Befehlen.

Erstens: Eingabedatei einlesen und die noch nicht geprüften Datensätze nach `output\unannotiert.csv` schreiben.

```powershell
uv run bookmatcher "data\Buchliste.xlsx"
```

Das Programm fragt dabei, ob eine manuelle Zeilenauswahl verwendet werden soll. Für den normalen Fall einfach `n` eingeben und Enter drücken; dann werden alle Datensätze übernommen.

Zweitens: K10plus-Matching für die unannotierten Datensätze ausführen.

```powershell
uv run python -m bookmatcher.batch output\unannotiert.csv output\unannotiert_matches.csv
```

Das Ergebnis steht anschließend in `output\unannotiert_matches.csv`.

## Schnellstart unter Linux

Die folgenden Schritte gehen davon aus, dass die Buchliste im Projektordner unter `data/Buchliste.xlsx` liegt. Wenn die Datei anders heißt, muss nur dieser Dateiname im ersten Arbeitsbefehl angepasst werden.

Einmalig das Setup starten:

```bash
bash scripts/setup-linux.sh
```

Danach besteht der normale Arbeitsablauf aus zwei Befehlen.

Erstens: Eingabedatei einlesen und die noch nicht geprüften Datensätze nach `output/unannotiert.csv` schreiben.

```bash
uv run bookmatcher "data/Buchliste.xlsx"
```

Das Programm fragt dabei, ob eine manuelle Zeilenauswahl verwendet werden soll. Für den normalen Fall einfach `n` eingeben und Enter drücken; dann werden alle Datensätze übernommen.

Zweitens: K10plus-Matching für die unannotierten Datensätze ausführen.

```bash
uv run python -m bookmatcher.batch output/unannotiert.csv output/unannotiert_matches.csv
```

Das Ergebnis steht anschließend in `output/unannotiert_matches.csv`.

## Automatisches Setup

Ein weitgehend automatisches Setup ist möglich und über die Skripte in `scripts/` vorbereitet. Sie verwenden den offiziellen [`uv`-Installer](https://docs.astral.sh/uv/getting-started/installation/), installieren `uv`, falls es noch fehlt, und führen danach `uv sync` aus; `uv` richtet die passende Python-Umgebung und alle Projektabhängigkeiten ein.

Grenzen des automatischen Setups: Der Rechner braucht Internetzugang, PowerShell muss lokale Skripte starten dürfen, und das spätere Matching benötigt Zugriff auf die K10plus-Schnittstelle. Unter Windows muss PowerShell nach dem Setup einmal neu geöffnet werden, damit der frisch ergänzte `uv`-Pfad sicher verfügbar ist.

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

Die Evaluation ist vor allem für Entwicklung und Qualitätskontrolle gedacht. Im praktischen Arbeitsablauf ohne vorhandene Ground Truth muss sie nicht ausgeführt werden.

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

Die hohe Precision bedeutet, dass gefundene Treffer sehr häufig mit der bisherigen manuellen Annotation übereinstimmen. Bei den wenigen False Positives ist anzunehmen, dass ein Teil auf nicht gefundene Treffer in der ursprünglichen Annotation zurückgeht; diese Fälle können bei Bedarf nachevaluiert werden und werden in der folgenden Tabelle aufgelistet. Der geringere Recall zeigt, dass die konservative Suchstrategie vorhandene Bücher teilweise nicht findet.

| Quellzeile | Lokaler Datensatz                                           | Gefundener Kandidat                                                            | Jahr-Distanz |
| ---------: | ----------------------------------------------------------- | ------------------------------------------------------------------------------ | -----------: |
|    **102** | Fischer, Rudolf — *August Schleicher zur Erinnerung* — 1962 | gleichnamiger Treffer, sogar **2 Katalogrecords von 1962**                     |        **0** |
|    **185** | Hossfeld, Fr. — *Geschichte des Dorfes Achelstädt* — 1905   | *Geschichte des Dorfes Achelstädt ; mit einem Kärtchen von Aug. Thomas* — 1905 |        **0** |
|    **207** | Karch, Dieter — *Zur Morphologie des Pfälzischen* — 1990    | *Zur Morphologie im Pfälzischen* — 1990                                        |        **0** |
|    **304** | Mills, Theodore M. — *the sociology of small groups* — 1967 | *Soziologie der Gruppe* — 1969                                                 |        **2** |
|    **349** | Riesel, Elise — *Stilistik der deutschen Sprache* — 1963    | *Stilistik der deutschen Sprache* — 1959                                       |        **4** |


## Hinweise für die manuelle Prüfung

TL;DR: Der erste Kandidat ist ein Vorschlag, keine Entscheidung. `year_distance = 0` ist ein starkes Signal, ersetzt aber nicht den Vergleich von Autor, Titel und Erscheinungsjahr. Unterschiedliche Vornamen, Zeichensetzung, Untertitel oder transliterierte Schreibweisen sind in bibliographischen Daten normal und sollten nicht allein zum Verwerfen führen. Wichtig ist außerdem die Unterscheidung zwischen gleichem Werk und gleicher Ausgabe, besonders bei häufig aufgelegten Titeln.
