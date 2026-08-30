#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv wurde nicht gefunden. Installation wird gestartet..."

    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh
    else
        echo "Fehler: Bitte zuerst curl oder wget installieren."
        exit 1
    fi

    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "Fehler: uv wurde installiert, ist aber noch nicht im PATH."
    echo "Bitte Terminal schliessen, neu oeffnen und dieses Setup erneut starten."
    exit 1
fi

echo "Installiere Python-Umgebung und Abhaengigkeiten..."
uv sync

echo
echo "Setup fertig."
echo
echo "Danach sind fuer den normalen Workflow zwei Befehle wichtig:"
echo '1. uv run bookmatcher "data/Buchliste.xlsx"'
echo '2. uv run python -m bookmatcher.batch output/unannotiert.csv output/unannotiert_matches.csv'
