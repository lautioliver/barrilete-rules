---
id: correr-los-comandos-reales
status: accepted
origin: observed
applies_to: [reviewer]
scope: "*"
classes: [wrong-command]
severity: fix
accepted: 2026-11-04
---
Si un skill, doc o PR indica un comando (flags, prefijos, rutas), correlo contra la herramienta real antes de darlo por bueno; no lo revises solo como texto.

## Por qué
Salió de desvíos reales de agentes y la persona la aprobó (lección aceptada de `bk learn`).

## Evidencia
- #237: `SKILL.md:50` buscaba el PR de un agente con `gh pr list --head claude/<n>-…`, pero `--head` solo acepta el nombre exacto de la rama. El orquestador nunca encontraba el PR ni lanzaba al reviewer. Las rondas 1 a 3 lo leyeron como texto y no lo corrieron.
- #240: el agente dijo que el CI fallaba "por azar" y que localmente pasaba, sin correr el test que fallaba (`test-init.sh` #78).

Origen: lección `lessons/reviewer-comandos-reales.md` del vault de `bk learn`, aceptada el 2026-11-04.
