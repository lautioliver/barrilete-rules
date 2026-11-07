---
id: aislar-el-sistema-real-antes-de-romper
status: accepted
origin: observed
applies_to: [implementer, reviewer]
scope: "*"
classes: []
severity: fix
accepted: 2026-11-05
---
Antes de romper código a propósito para ver si un test falla, aislá lo que toca el sistema real (tmux, red, archivos fuera del tmp) con un falso en PATH: con la guarda rota, el test corre en serio.

## Por qué
Salió de desvíos reales de agentes y la persona la aprobó (lección aceptada de `bk learn`).

## Evidencia
- 2026-11-05 14:37: cuatro workspaces vacíos (`bk-barrilete-workspace-5` a `-8`) en 8 segundos, uno con la persona conectada.
- El test confiaba en `--dry-run` para no tocar tmux: con la guarda rota, corrió en serio.
- Arreglo: c0d1280 (el test le pasa a bk un tmux falso que solo anota) y c46e40c (`--dry-run` en `bk chat` y `bk ws`).

Origen: lección `lessons/tests-aislar-el-sistema-real.md` del vault de `bk learn`, aceptada el 2026-11-05.
