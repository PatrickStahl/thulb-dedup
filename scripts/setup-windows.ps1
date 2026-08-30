$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

function Add-UvToCurrentPath {
    $Candidates = @(
        (Join-Path $HOME ".local\bin"),
        (Join-Path $HOME ".cargo\bin")
    )

    foreach ($Candidate in $Candidates) {
        $UvPath = Join-Path $Candidate "uv.exe"
        if (Test-Path $UvPath) {
            $PathParts = $env:Path -split ";"
            if ($PathParts -notcontains $Candidate) {
                $env:Path = "$Candidate;$env:Path"
            }
        }
    }
}

Add-UvToCurrentPath

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv wurde nicht gefunden. Installation wird gestartet..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    Add-UvToCurrentPath
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv wurde installiert, ist aber noch nicht im PATH. Bitte PowerShell schliessen, neu oeffnen und dieses Setup erneut starten."
}

Write-Host "Installiere Python-Umgebung und Abhaengigkeiten..."
uv sync

Write-Host ""
Write-Host "Setup fertig."
Write-Host ""
Write-Host "Danach sind fuer den normalen Workflow zwei Befehle wichtig:"
Write-Host '1. uv run bookmatcher "data\Buchliste.xlsx"'
Write-Host '2. uv run python -m bookmatcher.batch output\unannotiert.csv output\unannotiert_matches.csv'
