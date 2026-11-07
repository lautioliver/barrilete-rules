---
id: numeros-del-pr-desde-la-ultima-corrida
status: accepted
origin: observed
applies_to: [implementer]
scope: [barrilete-kit]
classes: [pr-metadata]
severity: fix
accepted: 2026-11-04
check: pr-metadata
fail_message: "El cuerpo del PR no coincide con la rama (red commit, casos, cantidad de commits o número del issue): regenerá esos números desde la última corrida con red.sh y git log, y corregí el cuerpo con gh pr edit. Si el check sigue fallando y creés que se equivoca, escalá y no cambies el check."
---
Antes de pedir review, regenerá los números del cuerpo del PR (casos, commits, SHA) desde la última corrida; no los copies de una anterior.

## Por qué
Salió de desvíos reales de agentes y la persona la aprobó (lección aceptada de `bk learn`).

## Evidencia
Origen: lección `lessons/hallazgo-de-review-metadatos-del-pr.md` del vault de `bk learn`, aceptada el 2026-11-04.
