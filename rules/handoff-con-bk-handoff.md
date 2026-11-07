---
id: handoff-con-bk-handoff
status: accepted
origin: observed
applies_to: "*"
scope: "*"
classes: []
severity: fix
accepted: 2026-11-05
---
Para dejar un resumen para seguir en otra sesión, corré `bk handoff` y seguí su plantilla y su archivo; no armes uno a mano con otro formato.

## Por qué
Salió de desvíos reales de agentes y la persona la aprobó (lección aceptada de `bk learn`).

## Evidencia
- 2026-11-05: el resumen de #262 que se pegó para abrir esta sesión no tenía sesión, rama ni cuenta, y no quedó en ningún archivo.
- `~/.local/state/bk/handoffs/` no existía: el formato no se había usado nunca.

Origen: lección `lessons/resumen-para-seguir-con-handoff.md` del vault de `bk learn`, aceptada el 2026-11-05.
