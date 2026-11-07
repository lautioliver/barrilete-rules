---
id: scripts-que-escriben-en-git-con-worktree-y-concurrencia
status: accepted
origin: human
applies_to: [implementer]
scope: [barrilete-kit]
classes: []
severity: suggestion
accepted: 2026-10-01
---
Scripts that write to `.git` are also tested from a `git worktree` and with concurrent writes in all the ones they do, not just the one the issue names: agents run in worktrees and in parallel (pending retros lost with `git worktree remove`; `.git/config` lock in `worktree add`).

## Por qué
Es una lección de los retros del kit que revisó una persona en un PR de `/improve-skills`: contexto, no una regla que bloquee.

## Evidencia
#39, #40.

Origen: línea de docs/agents/lessons.md del kit (2026-10); la fecha `accepted` es el primer día del mes porque el archivo solo guarda el mes.
