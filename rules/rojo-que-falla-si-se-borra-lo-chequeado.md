---
id: rojo-que-falla-si-se-borra-lo-chequeado
status: accepted
origin: observed
applies_to: [implementer]
scope: [barrilete-kit]
classes: [test-cannot-fail]
severity: fix
accepted: 2026-11-04
---
En el rojo, probá que cada caso nuevo falle si borrás lo que chequea; sin `grep … && grep …`, `! grep` ni `except: pass`.

## Por qué
Salió de desvíos reales de agentes y la persona la aprobó (lección aceptada de `bk learn`).

## Evidencia
Origen: lección `lessons/hallazgo-de-review-test-que-no-puede-fallar.md` del vault de `bk learn`, aceptada el 2026-11-04.
