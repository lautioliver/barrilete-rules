---
id: arreglo-sin-agujeros
status: accepted
origin: observed
applies_to: [implementer]
scope: "*"
classes: [unhandled-input]
severity: fix
accepted: 2026-11-01
---
Después de cada arreglo, buscá qué rompe: complejidad (regex, loops), entradas hostiles y cambios fuera de alcance.

## Por qué
Salió de desvíos reales de agentes y la persona la aprobó (lección aceptada de `bk learn`).

## Evidencia
- #143: el arreglo hizo que la regex de `no tests:` tome tiempo cúbico sobre un cuerpo que controla el autor.
- #173: un cambio fuera de alcance en el mensaje de crash de tap_run deshizo los diagnósticos de #77.
- #166: el loop nuevo abrió un agujero en stdin.

Origen: lección `lessons/implementer-arreglo-sin-agujeros.md` del vault de `bk learn`, aceptada el 2026-11-01.
