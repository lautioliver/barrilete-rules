---
id: revisar-que-el-test-falle
status: accepted
origin: observed
applies_to: [reviewer]
scope: "*"
classes: [test-cannot-fail]
severity: fix
accepted: 2026-11-04
---
Al revisar, probá que cada test nuevo falle si quitás o rompés lo que chequea (borrá el archivo, comentá la línea); si pasa igual, es un hallazgo a corregir.

## Por qué
Salió de desvíos reales de agentes y la persona la aprobó (lección aceptada de `bk learn`).

## Evidencia
- #237, 4.ª ronda: los casos nuevos de `test-orchestrate.sh:315` y `:319` (`! grep`, `grep … ||`) pasan aunque el ADR o el SKILL no existan. Las rondas 1 a 3 no lo vieron.
- #238: el `trap - ERR` en los subshells escondía un crash del helper; un caso pasaba crasheara o no.
- #241: el test del "mapa válido" pasaba aunque la validación nueva no corriera.

Origen: lección `lessons/reviewer-test-que-falla.md` del vault de `bk learn`, aceptada el 2026-11-04.
