# bookmatcher – Stage 1

Erster Schritt des ThULB-Abgleichs: CSV- oder Excel-Datei laden, anhand der bestehenden
ThULB-Spalte in annotierte und unannotierte Datensätze teilen und beide Gruppen
als eigene CSV-Dateien exportieren.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
```

## Verwendung

```bash
bookmatcher "data/Buchliste Archiv_neu_fortlaufend.xlsx"
```

Standardmäßig werden alle automatisch erkannten annotierten und unannotierten
Datensätze exportiert. Die interaktive Abfrage erlaubt optional eine Auswahl
anhand der ursprünglichen Eingabe-Zeilennummern.

Nicht-interaktiv:

```bash
bookmatcher "data/Buchliste Archiv_neu_fortlaufend.xlsx" --no-prompt
```

Ausgabe:

```text
output/
├── annotiert.csv
└── unannotiert.csv
```
