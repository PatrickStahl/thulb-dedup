$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

function Get-UvInstallDir {
    $Candidates = @(
        (Join-Path $HOME ".local\bin"),
        (Join-Path $HOME ".cargo\bin")
    )

    foreach ($Candidate in $Candidates) {
        $UvPath = Join-Path $Candidate "uv.exe"
        if (Test-Path $UvPath) {
            return $Candidate
        }
    }

    return $null
}

function Add-UvToPath {
    param(
        [Parameter(Mandatory = $true)]
        [string] $UvInstallDir
    )

    $CurrentPathParts = $env:Path -split ";"
    if ($CurrentPathParts -notcontains $UvInstallDir) {
        $env:Path = "$UvInstallDir;$env:Path"
    }

    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $UserPathParts = @()
    if ($UserPath) {
        $UserPathParts = $UserPath -split ";"
    }

    if ($UserPathParts -notcontains $UvInstallDir) {
        $NewUserPath = if ($UserPath) {
            "$UvInstallDir;$UserPath"
        }
        else {
            $UvInstallDir
        }

        [Environment]::SetEnvironmentVariable("Path", $NewUserPath, "User")
    }
}

$UvInstallDir = Get-UvInstallDir
if ($UvInstallDir) {
    Add-UvToPath -UvInstallDir $UvInstallDir
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv wurde nicht gefunden. Installation wird gestartet..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    $UvInstallDir = Get-UvInstallDir
    if ($UvInstallDir) {
        Add-UvToPath -UvInstallDir $UvInstallDir
    }
}

$UvCommand = Get-Command uv -ErrorAction SilentlyContinue

if (-not $UvCommand -and $UvInstallDir) {
    $UvCommand = Get-Command (Join-Path $UvInstallDir "uv.exe") -ErrorAction SilentlyContinue
}

if (-not $UvCommand) {
    throw "uv wurde installiert, ist aber noch nicht im PATH. Bitte PowerShell schliessen, neu oeffnen und dieses Setup erneut starten."
}

Write-Host "Installiere Python-Umgebung und Abhaengigkeiten..."
& $UvCommand.Source sync

Write-Host ""
Write-Host "Setup fertig."
Write-Host "Bitte dieses PowerShell-Fenster schliessen und im Projektordner neu oeffnen,"
Write-Host "damit der Befehl 'uv' verfuegbar ist."
Write-Host ""
Write-Host "Danach sind fuer den normalen Workflow zwei Befehle wichtig:"
Write-Host '1. uv run bookmatcher "data\Buchliste.xlsx"'
Write-Host '2. uv run python -m bookmatcher.batch output\unannotiert.csv output\unannotiert_matches.csv'
