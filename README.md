# barrilete-rules

Las reglas que siguen los agentes de Barrilete, una por archivo. Es el almacén de [ADR-006 del kit](https://github.com/lautioliver/barrilete-kit/blob/main/docs/decisions/kit/ADR-006-rules-store-for-agents.md): reemplaza a docs/agents/lessons.md del kit y a las lecciones de `bk learn`.

## Qué hay

- `rules/<id>.md`: una regla por archivo.
- `classes.yml`: las clases de hallazgo y de desvío. Este repo es su única fuente.
- `scripts/validate.py`: el validador que corre el CI.

No hay `checks/`: los checks se implementan en el kit (`scripts/agents/checks/<id>`); una regla solo declara `check: <id>` y su `fail_message`. Tampoco hay desvíos: quedan locales en `bk learn` y nunca entran a este repo.

## Formato de una regla

Un archivo `rules/<id>.md`. Arriba, el frontmatter; abajo, en una línea la regla, después el porqué y la evidencia (de dónde viene).

| campo | valores |
|---|---|
| `id` | slug en minúsculas, igual al nombre del archivo; sin números secuenciales |
| `status` | `proposed`, `accepted` o `deprecated`. Solo `accepted` se inyecta |
| `origin` | `observed`, `human` o `general`. `general` solo con `classes` o `check` |
| `applies_to` | roles (`implementer`, `reviewer`…) o `"*"` |
| `scope` | `"*"` o repos (`barrilete-kit`) |
| `classes` | ids de `classes.yml` (puede ser `[]`) |
| `check` | opcional: id de un check del kit. Con `check` va `fail_message` |
| `severity` | `block`, `fix` o `suggestion`. `block` exige `check` |
| `accepted` | fecha ISO. Obligatoria si `status: accepted` |
| `examples` | opcional: casos `bad` y `good` |

## Cómo se acepta una regla

Mergeando el PR que la agrega o que la pasa a `accepted`: así una persona siempre la revisa. El CI corre el validador:

```bash
python3 scripts/validate.py          # valida el repo
python3 -m unittest discover tests   # tests del validador
```

El validador rechaza archivos fuera de `rules/`, `classes.yml`, la documentación y las herramientas (`scripts/`, `tests/`, `.github/`).
