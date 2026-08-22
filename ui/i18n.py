from __future__ import annotations

from PySide6.QtCore import QLocale

from engine.prefs import load_language

_LANG = "en"

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "tab_live": "Live",
        "tab_diag": "Diagnosis",
        "tab_settings": "Settings",
        "device": "Device",
        "drivers": "Drivers",
        "save_profile": "Save profile",
        "virtual_on": "Enable virtual controller",
        "virtual_off": "Stop virtual controller",
        "no_pad": "No pad selected",
        "profile_none": "Profile: none (defaults)",
        "profile_named": "Profile: {name}",
        "stick_left": "Left stick (filtered)",
        "stick_right": "Right stick (filtered)",
        "buttons": "Buttons",
        "ls_dz": "LS deadzone %",
        "rs_dz": "RS deadzone %",
        "curve": "Stick curve (100 = linear)",
        "invert_ly": "Invert LY",
        "invert_ry": "Invert RY",
        "recenter": "Recenter sticks",
        "remap_sources": "Remap sources (multi-select)",
        "destination": "Destination",
        "hold_none": "No hold toggle",
        "hold_item": "Hold {label} toggles",
        "add_remap": "Add remap",
        "del_remap": "Remove remap",
        "run_diag": "Run diagnosis",
        "apply_diag": "Apply recommendations",
        "diag_steps": "1. Keep still   2. Full stick circles   3. Full triggers",
        "diag_idle": "Idle",
        "diag_started": "Diagnosis started...",
        "diag_rest": "Keep the pad still ({t:.1f}s)",
        "diag_range": "Move both sticks in full circles ({t:.1f}s)",
        "diag_triggers": "Press LT and RT all the way ({t:.1f}s)",
        "diag_done": "Done — score {score}/100",
        "diag_score": "Score {score}/100",
        "language": "Language",
        "lang_system": "System default",
        "lang_en": "English",
        "lang_es": "Spanish",
        "driver_ok": "OK",
        "driver_missing": "missing",
        "ps3_ok": "PS3: {name} OK",
        "ps3_missing": "PS3: {name} missing",
        "virtual_stopped": "Virtual pad stopped",
        "select_pad": "Select a pad first",
        "virtual_running": "Virtual Xbox 360 running. {note}",
        "disconnected": "Disconnected",
        "live_pad": "Live: {name}{extra}",
        "profile_loaded": "  profile loaded",
        "vigem_body": (
            "ViGEmBus is required for the virtual pad.\n"
            "Download the official setup from Nefarius and install it?\n"
            "Windows will ask for administrator permission."
        ),
        "hidhide_body": (
            "HidHide hides the physical pad so games only see the virtual one.\n"
            "Download the official setup from Nefarius and install it?\n"
            "Windows will ask for administrator permission."
        ),
        "ps3_dshidmini": (
            "A DualShock 3 was detected. Windows 10/11 works best with "
            "the official Nefarius DsHidMini driver.\n"
            "Download and install it now? Windows will ask for administrator permission."
        ),
        "ps3_scp": (
            "A DualShock 3 was detected. On this Windows version the "
            "supported helper is the official Nefarius ScpToolkit "
            "(archived; last release).\n"
            "Download and install it now? Windows will ask for administrator permission."
        ),
        "dl_setup": "Downloading official {name} setup...",
        "finish_vigem": "Finish the ViGEmBus installer, then activate the virtual pad again.",
        "finish_hidhide": "Finish the HidHide installer, then activate the virtual pad again.",
        "finish_ps3": "Finish the {name} installer, then reconnect the DualShock 3.",
        "saved": "Saved {name}",
        "select_remap": "Select at least one source and a destination",
        "centers": "Stick centers captured",
        "run_diag_first": "Run diagnosis first",
        "applied_diag": "Applied diagnosis recommendations",
        "virtual_err": "Virtual pad: {error}",
        "hide_missing": "HidHide missing: games will see two pads.",
        "hide_xinput": "HidHide on, but no HID path to hide (XInput-only).",
        "hide_ok": "Physical pad hidden from other apps.",
        "hide_fail": "HidHide failed ({error}). Games may see two pads.",
        "rec_deadzone": "Set {name} deadzone to {pct}%",
        "rec_recenter": "Recenter {name} (offset {offset:.3f})",
        "rec_range": "{name} does not reach full throw ({peak:.2f})",
        "rec_trigger": "{name} does not reach 100% ({peak:.2f})",
        "rec_none": "No changes needed",
        "rec_rest_again": "Run the rest step again",
        "yes": "Yes",
        "no": "No",
    },
    "es": {
        "tab_live": "En vivo",
        "tab_diag": "Diagnóstico",
        "tab_settings": "Ajustes",
        "device": "Dispositivo",
        "drivers": "Drivers",
        "save_profile": "Guardar perfil",
        "virtual_on": "Activar mando virtual",
        "virtual_off": "Parar mando virtual",
        "no_pad": "Ningún mando seleccionado",
        "profile_none": "Perfil: ninguno (valores por defecto)",
        "profile_named": "Perfil: {name}",
        "stick_left": "Stick izquierdo (filtrado)",
        "stick_right": "Stick derecho (filtrado)",
        "buttons": "Botones",
        "ls_dz": "Zona muerta LI %",
        "rs_dz": "Zona muerta LD %",
        "curve": "Curva de sticks (100 = lineal)",
        "invert_ly": "Invertir LY",
        "invert_ry": "Invertir RY",
        "recenter": "Recentrar sticks",
        "remap_sources": "Orígenes del remap (selección múltiple)",
        "destination": "Destino",
        "hold_none": "Sin toggle al mantener",
        "hold_item": "Mantener {label} alterna",
        "add_remap": "Añadir remap",
        "del_remap": "Quitar remap",
        "run_diag": "Ejecutar diagnóstico",
        "apply_diag": "Aplicar recomendaciones",
        "diag_steps": "1. Quieto   2. Círculos completos   3. Gatillos a fondo",
        "diag_idle": "En espera",
        "diag_started": "Diagnóstico iniciado...",
        "diag_rest": "Mantené el mando quieto ({t:.1f}s)",
        "diag_range": "Mové ambos sticks en círculos completos ({t:.1f}s)",
        "diag_triggers": "Apretá LT y RT a fondo ({t:.1f}s)",
        "diag_done": "Listo — puntaje {score}/100",
        "diag_score": "Puntaje {score}/100",
        "language": "Idioma",
        "lang_system": "Idioma del sistema",
        "lang_en": "Inglés",
        "lang_es": "Español",
        "driver_ok": "OK",
        "driver_missing": "faltante",
        "ps3_ok": "PS3: {name} OK",
        "ps3_missing": "PS3: {name} faltante",
        "virtual_stopped": "Mando virtual detenido",
        "select_pad": "Elegí un mando primero",
        "virtual_running": "Xbox 360 virtual activo. {note}",
        "disconnected": "Desconectado",
        "live_pad": "En vivo: {name}{extra}",
        "profile_loaded": "  perfil cargado",
        "vigem_body": (
            "ViGEmBus es necesario para el mando virtual.\n"
            "¿Descargar el instalador oficial de Nefarius e instalarlo?\n"
            "Windows va a pedir permiso de administrador."
        ),
        "hidhide_body": (
            "HidHide oculta el mando físico para que el juego solo vea el virtual.\n"
            "¿Descargar el instalador oficial de Nefarius e instalarlo?\n"
            "Windows va a pedir permiso de administrador."
        ),
        "ps3_dshidmini": (
            "Se detectó un DualShock 3. En Windows 10/11 conviene el driver "
            "oficial Nefarius DsHidMini.\n"
            "¿Descargarlo e instalarlo ahora? Windows va a pedir permiso de administrador."
        ),
        "ps3_scp": (
            "Se detectó un DualShock 3. En esta versión de Windows el helper "
            "soportado es ScpToolkit de Nefarius (archivado; último release).\n"
            "¿Descargarlo e instalarlo ahora? Windows va a pedir permiso de administrador."
        ),
        "dl_setup": "Descargando el setup oficial de {name}...",
        "finish_vigem": "Terminá el instalador de ViGEmBus y volvé a activar el mando virtual.",
        "finish_hidhide": "Terminá el instalador de HidHide y volvé a activar el mando virtual.",
        "finish_ps3": "Terminá el instalador de {name} y reconectá el DualShock 3.",
        "saved": "Guardado {name}",
        "select_remap": "Elegí al menos un origen y un destino",
        "centers": "Centros de sticks capturados",
        "run_diag_first": "Ejecutá el diagnóstico primero",
        "applied_diag": "Recomendaciones del diagnóstico aplicadas",
        "virtual_err": "Mando virtual: {error}",
        "hide_missing": "Falta HidHide: los juegos van a ver dos mandos.",
        "hide_xinput": "HidHide activo, pero no hay ruta HID para ocultar (solo XInput).",
        "hide_ok": "Mando físico oculto para otras apps.",
        "hide_fail": "HidHide falló ({error}). Los juegos pueden ver dos mandos.",
        "rec_deadzone": "Poner zona muerta de {name} en {pct}%",
        "rec_recenter": "Recentrar {name} (offset {offset:.3f})",
        "rec_range": "{name} no llega al recorrido completo ({peak:.2f})",
        "rec_trigger": "{name} no llega al 100% ({peak:.2f})",
        "rec_none": "No hace falta cambiar nada",
        "rec_rest_again": "Repetí el paso en reposo",
        "yes": "Sí",
        "no": "No",
    },
}


def system_language() -> str:
    name = QLocale.system().name().lower()
    return "es" if name.startswith("es") else "en"


def resolved_language(preference: str | None = None) -> str:
    pref = preference if preference is not None else load_language()
    if pref in {"en", "es"}:
        return pref
    return system_language()


def set_language(preference: str) -> None:
    global _LANG
    _LANG = resolved_language(preference)


def current_language() -> str:
    return _LANG


def tr(key: str, **kwargs: object) -> str:
    table = _STRINGS.get(_LANG) or _STRINGS["en"]
    text = table.get(key) or _STRINGS["en"].get(key) or key
    if kwargs:
        return text.format(**kwargs)
    return text


set_language(load_language())
