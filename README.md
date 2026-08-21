# joystick-doctor

Diagnóstico y calibración de joysticks en Windows: drift, remap/combos y un mando Xbox 360 virtual.

## Requisitos

- Windows 10/11
- Python 3.10+
- [ViGEmBus](https://github.com/nefarius/ViGEmBus/releases) (salida virtual)
- [HidHide](https://github.com/nefarius/HidHide/releases) (ocultar el mando físico; a menudo hace falta ejecutar como administrador al configurarlo)

XInput (Xbox) se lee con `xinput1_4.dll` vía ctypes; no hay paquete extra.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

La UI y el loop virtual todavía no están; `main.py` es el punto de entrada.
