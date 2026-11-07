---
id: code-review-hallazgos-pueden-ser-falsos
status: accepted
origin: human
applies_to: [implementer]
scope: [barrilete-kit]
classes: []
severity: suggestion
accepted: 2026-10-01
---
Check the `/code-review` findings before fixing or classifying them: they can be false (in #39, `commit-tree` does not respect `commit.gpgSign`).

## Por qué
Es una lección de los retros del kit que revisó una persona en un PR de `/improve-skills`: contexto, no una regla que bloquee.

## Evidencia
#39, #40.

Origen: línea de docs/agents/lessons.md del kit (2026-10); la fecha `accepted` es el primer día del mes porque el archivo solo guarda el mes.
