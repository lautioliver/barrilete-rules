---
id: tests-de-shell-sin-framework
status: accepted
origin: human
applies_to: [implementer]
scope: [barrilete-kit]
classes: []
severity: suggestion
accepted: 2026-10-01
---
To test shell scripts without a framework: a local bare remote and a fake `gh` in the `PATH`, isolated from the global git config. Models: `.claude/skills/improve-skills/test-retros.sh` and `.claude/skills/implement-issue/test-prepare.sh`.

## Por qué
Es una lección de los retros del kit que revisó una persona en un PR de `/improve-skills`: contexto, no una regla que bloquee.

## Evidencia
#39, #40.

Origen: línea de docs/agents/lessons.md del kit (2026-10); la fecha `accepted` es el primer día del mes porque el archivo solo guarda el mes.
