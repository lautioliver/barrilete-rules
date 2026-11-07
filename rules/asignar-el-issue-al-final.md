---
id: asignar-el-issue-al-final
status: accepted
origin: human
applies_to: [implementer]
scope: [barrilete-kit]
classes: []
severity: suggestion
accepted: 2026-10-01
---
In the scripts that take an issue, assign at the end, after everything that can fail: if it fails before, the issue stays assigned with no work done.

## Por qué
Es una lección de los retros del kit que revisó una persona en un PR de `/improve-skills`: contexto, no una regla que bloquee.

## Evidencia
#40.

Origen: línea de docs/agents/lessons.md del kit (2026-10); la fecha `accepted` es el primer día del mes porque el archivo solo guarda el mes.
