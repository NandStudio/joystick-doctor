$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    python -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-build.txt
.\.venv\Scripts\pyinstaller.exe --noconfirm --clean .\packaging\joystick-doctor.spec

$payload = Join-Path $root "dist\JoystickDoctor\JoystickDoctor.exe"
if (-not (Test-Path $payload)) {
    throw "PyInstaller did not produce $payload"
}

function Find-ISCC {
    $cmd = Get-Command iscc -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "${env:LocalAppData}\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) {
            return $path
        }
    }
    return $null
}

$iscc = Find-ISCC
if (-not $iscc) {
    Write-Host "PyInstaller folder: $root\dist\JoystickDoctor"
    throw "Inno Setup 6 not found. Install it and re-run, or compile packaging\joystick-doctor.iss from the Inno IDE."
}

& $iscc ".\packaging\joystick-doctor.iss"
if ($LASTEXITCODE -ne 0) {
    throw "ISCC failed with exit $LASTEXITCODE"
}

Write-Host "Installer: $root\dist\JoystickDoctorSetup-0.1.0.exe"
Write-Host "The setup copies the app only. ViGEmBus / HidHide / DsHidMini still install from inside the app."
