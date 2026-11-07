---
id: un-worktree-por-agente
status: accepted
origin: human
applies_to: [implementer]
scope: [barrilete-kit]
classes: []
severity: suggestion
accepted: 2026-11-01
---
One worktree per agent, also for the `implementer` that a review launches: `prepare.sh <n> --worktree` takes a lock (`agent-lock`) and refuses a worktree with a live owner; the one who arrives second stops and reports, it does not share the branch.

## Por qué
Es una lección de los retros del kit que revisó una persona en un PR de `/improve-skills`: contexto, no una regla que bloquee.

## Evidencia
#267.

Origen: línea de docs/agents/lessons.md del kit (2026-11); la fecha `accepted` es el primer día del mes porque el archivo solo guarda el mes.
