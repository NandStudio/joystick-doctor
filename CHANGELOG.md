# 0.2.3

## Mandos

Un mando que no es Xbox ya no se abre como el jugador 1 de XInput. Se lee su informe HID, con sticks, botones y gatillos.

El gatillo que reposa en el centro se parte en LT y RT. El adaptador `0810:0001` se lee con el reporte de un control de PS1.

El DualShock 3 que DsHidMini presenta como Xbox One se vuelve a leer como DualShock 3, y L2 y R2 salen de la presión real. Un USB Gamepad genérico que usa ese mismo identificador no se renombra a DualShock 3: queda en el lector genérico.

En Sistema, con un mando genérico abierto, se puede elegir el mapeo. Las opciones son Genérico, DualShock 3 A1 WC y DBlue. El A1 WC y el DBlue (`0079:0006`, el USB Joystick de Microntek) se eligen solos cuando el descriptor coincide. La elección queda guardada para ese mando.

Un puerto que no cambia de estado deja de soltar el mando que se está usando.

## Sistema

La pantalla Sistema se desplaza. Explica DsHidMini, permite instalarlo y guardar el modo del driver. Acerca de agradece a Nefarius por DsHidMini, junto a ViGEmBus e HidHide.

La búsqueda de actualizaciones y la descarga de drivers confían en el certificado de GitHub.

## Diagnóstico

Con el modo debug activo, el registro anota el descriptor y los reportes de un mando genérico que todavía no tiene mapeo. Esos mismos datos entran en el log de un fallo, aunque el debug esté apagado. El stick izquierdo y el temblor del reposo no llenan el registro.

## Icono

El icono de la ventana, Alt+Tab y la barra de tareas sigue el tema claro u oscuro de Windows. El acceso directo del escritorio usa el icono claro.
