---
id: arreglar-la-clase-de-casos
status: accepted
origin: observed
applies_to: [implementer]
scope: "*"
classes: [uncovered-case]
severity: fix
accepted: 2026-11-01
---
Al cerrar un bloqueante, arreglá la clase de casos, no solo los ejemplos: probá variantes (pipelines, subshells, funciones, `sh -c`, backticks) antes de declarar una lista completa.

## Por qué
Salió de desvíos reales de agentes y la persona la aprobó (lección aceptada de `bk learn`).

## Evidencia
- #165 (dos rondas): pipelines, subshells, funciones y luego 3 formas naturales más seguían dando un rojo válido con crash.
- #170: la lista de formas prohibidas dejaba afuera backticks y `sh -c` con varios comandos.
- #173: la lista de variantes que tap_run no atrapa se presentaba completa y no lo era.

Origen: lección `lessons/implementer-clase-no-ejemplo.md` del vault de `bk learn`, aceptada el 2026-11-01.
