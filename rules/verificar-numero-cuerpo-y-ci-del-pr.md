---
id: verificar-numero-cuerpo-y-ci-del-pr
status: accepted
origin: observed
applies_to: [implementer]
scope: "*"
classes: [pr-metadata, ci-claim]
severity: fix
accepted: 2026-11-01
---
Antes de pedir review, verificá número de PR vs issue, que el cuerpo del PR sea el tuyo y que lo que afirmás del CI sea cierto.

## Por qué
Salió de desvíos reales de agentes y la persona la aprobó (lección aceptada de `bk learn`).

## Evidencia
- #158: el ADR cita "PR #158" pero #158 es el issue y el PR es #159.
- #151: el cuerpo del PR se pisó con el de #164 (terminaba en `Closes #150`).
- #115: el PR afirmaba que su CI corrió la regex nueva, y no era cierto.

Origen: lección `lessons/implementer-metadatos-pr.md` del vault de `bk learn`, aceptada el 2026-11-01.
