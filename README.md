# joystick-doctor

App de escritorio para Windows: diagnosticar y calibrar un mando, aplicar deadzone/curvas/remap y usarlo como **Xbox 360 virtual** (ViGEmBus). El físico se puede ocultar con HidHide para que el juego no vea dos pads.

## Requisitos

- Windows 10/11
- Python 3.10+
- [ViGEmBus](https://github.com/nefarius/ViGEmBus/releases) — salida virtual
- [HidHide](https://github.com/nefarius/HidHide/releases) — ocultar el mando físico (suele pedir administrador)

La app puede descargar e iniciar los instaladores oficiales de Nefarius si faltan (ViGEmBus, HidHide). Si detecta un DualShock 3 oficial y no hay driver, ofrece **DsHidMini** en Windows 10/11 o **ScpToolkit** en Windows 7/8 (setup archivado de Nefarius). XInput se lee con `xinput1_4.dll`; no hace falta paquete extra.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Dependencias: `hidapi`, `vgamepad`, `PySide6`.

## Mandos

| Familia | Cómo se lee |
| --- | --- |
| Xbox / XInput | `xinput1_4` |
| DualShock 3 / clones USB tipo PS3 | HID (`ds3`; en USB oficial se habilita el reporte Sony) |
| DualShock 4 | HID |
| DualSense | HID |
| Switch Pro | HID (handshake USB) |
| HID genérico | fallback |

Un DualShock 3 oficial (`054C:0268`) en Windows 10/11 suele necesitar [DsHidMini](https://github.com/nefarius/DsHidMini); en Windows 7/8, [ScpToolkit](https://github.com/nefarius/ScpToolkit/releases) (proyecto archivado). La app lo propone al detectar el mando. Si el helper queda en modo XInput, aparece como XInput y no se duplica.

## Uso

1. Conectar el mando y elegirlo en la lista (izquierda).
2. **Live** — sticks, gatillos y botones ya filtrados.
3. **Diagnosis** — reposo → círculos de sticks → gatillos; aplica recomendaciones de deadzone/centro.
4. **Settings** — deadzone, curva, invertir Y, recentrar, remap/combos (hold opcional).
5. **Activar mando virtual** — Xbox 360 via ViGEm; HidHide oculta el físico si está instalado.

Los perfiles se guardan en `%LOCALAPPDATA%\joystick-doctor\profiles\`.
