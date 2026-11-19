#!/usr/bin/env python3
"""Valida barrilete-rules (ADR-006 D2, D3, D5 del kit).

Uso: python3 scripts/validate.py [<raíz>]   (por defecto, la raíz del repo)

Revisa cada rules/<id>.md y classes.yml, y que no haya archivos fuera de lo permitido.
No comprueba que el `check` de una regla exista: no vive acá, lo comprueba `sync-rules` en el kit (D7).
Sale con 0 si todo está bien, con 1 si hay errores (los imprime uno por línea), con 64 si el uso es inválido.
Solo usa la biblioteca estándar: el frontmatter es un YAML mínimo (`clave: valor`, listas en línea `[a, b]`).
"""
import datetime
import re
import subprocess
import sys
from pathlib import Path

STATUS = {"proposed", "accepted", "deprecated"}
ORIGIN = {"observed", "human", "general"}
SEVERITY = {"block", "fix", "suggestion"}
REQUIRED = ["id", "status", "origin", "applies_to", "scope", "classes", "severity"]
OPTIONAL = {"check", "fail_message", "accepted", "examples"}
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# La lista `deviations` de classes.yml se lee con el criterio del lector del kit (scripts/agents/check-docs.py), que recibe
# el archivo tal cual por `sync-rules`: lo que pasa acá tiene que pasar allá.
# Un tipo de desvío es un slug que empieza con una letra y no es una palabra que YAML 1.1 lee como booleano o null.
TIPO = re.compile(r"[a-z][a-z0-9]*(-[a-z0-9]+)*")
YAML11 = {"y", "n", "yes", "no", "true", "false", "on", "off", "null"}
# Una línea que empieza con la clave, bien o mal escrita: otra indentación, mayúsculas, comillas, `- ` delante, sin `:`.
DEV_KEY = re.compile(r"\s*(?:-\s*)?[\"']?deviations", re.I)
# La única forma válida. Sin corchetes ni `#` dentro de la lista; después de `]`, solo espacios.
DEV_LINE = re.compile(r"  deviations: \[([^\[\]#]*)\] *")
# Fuera de rules/ y classes.yml solo entran la documentación y las herramientas del validador.
ALLOWED_DIRS = ("rules/", "docs/", "scripts/", "tests/", ".github/")
ALLOWED_ROOT = {"classes.yml", ".gitignore", "LICENSE"}


def parse_value(raw):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [parse_value(p) for p in raw[1:-1].split(",") if p.strip()]
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def parse_frontmatter(text):
    """Devuelve (campos, error). `examples` puede tener un bloque indentado: se ignora el contenido."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, "no empieza con el frontmatter (---)"
    fields = {}
    for i, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return fields, None
        if not line.strip() or line.lstrip().startswith("#") or line[0] in " \t":
            continue
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if not m:
            return None, f"línea {i} del frontmatter no es `clave: valor`"
        if m.group(1) in fields:
            return None, f"el campo {m.group(1)} está repetido"
        fields[m.group(1)] = parse_value(re.sub(r"\s+#.*$", "", m.group(2)))
    return None, "el frontmatter no cierra (---)"


def mostrar(texto, tope=40):
    """Un texto del archivo para un mensaje: cortado a `tope` y sin caracteres de control ni invisibles (como los escribe repr)."""
    return repr(texto if len(texto) <= tope else texto[:tope] + "…")[1:-1]


def load_classes(path):
    """Ids de classes.yml: líneas `- id: <slug>`. Devuelve (ids, errores).

    Cada clase puede llevar `  deviations: [<tipo>, …]`: los tipos de desvío que le corresponden (ADR-007 D5 del kit).
    La línea se escribe exactamente así (dos espacios de indentación, un espacio después de `:`, lista en línea y nada más)
    y un tipo cae en una sola clase como máximo."""
    ids, errors = set(), []
    current, with_list, owner = None, set(), {}
    for n, line in enumerate(path.read_text(encoding="utf-8").split("\n"), start=1):
        m = re.match(r"^- id:\s*(\S+)\s*$", line)
        if m:
            if not SLUG.match(m.group(1)):
                errors.append(f"classes.yml:{n}: la clase {m.group(1)!r} no es un slug")
            if m.group(1) in ids:
                errors.append(f"classes.yml:{n}: la clase {m.group(1)} está repetida")
            ids.add(m.group(1))
            current = m.group(1)
            continue
        # El lector del kit corta las líneas donde corta str.splitlines() (FF, U+2028…), no solo en el salto de línea: una
        # clave detrás de uno de esos cortes es para él una línea aparte, así que acá también cuenta.
        if not any(DEV_KEY.match(parte) for parte in line.splitlines()):
            continue
        if not line.startswith("  deviations:"):
            errors.append(f"classes.yml:{n}: línea inesperada con la clave deviations (se espera exactamente "
                          "`  deviations: [<tipo>, …]`: dos espacios de indentación, en minúsculas, sin comillas y en su propia línea)")
            continue
        if current is None:
            errors.append(f"classes.yml:{n}: deviations fuera de una clase (va debajo de `- id:`)")
            continue
        if current in with_list:
            errors.append(f"classes.yml:{n}: la clase {current} tiene dos listas deviations")
            continue
        with_list.add(current)
        d = DEV_LINE.fullmatch(line)
        if not d:
            errors.append(f"classes.yml:{n}: deviations tiene que ser una lista en línea (se espera `  deviations: [<tipo>, …]`: "
                          "un solo espacio después de `:`, sin otro corchete ni comentario, y nada después de `]`)")
            continue
        seen = set()
        dentro = d.group(1).strip(" ")  # `[]` y `[ ]` son una lista sin tipos
        for t in [p.strip(" ") for p in dentro.split(",")] if dentro else []:
            if not t:
                errors.append(f"classes.yml:{n}: deviations de la clase {current} tiene un elemento vacío (una coma de más)")
            elif not TIPO.fullmatch(t):
                errors.append(f"classes.yml:{n}: el tipo de desvío '{mostrar(t)}' no es un slug que empieza con una letra "
                              "(minúsculas, números y guiones)")
            elif t in YAML11:
                errors.append(f"classes.yml:{n}: el tipo de desvío {t} es un booleano o null en YAML 1.1 (un parser YAML no lo "
                              "lee como texto): elegí otro tipo")
            elif t in seen:
                errors.append(f"classes.yml:{n}: el tipo de desvío {mostrar(t)} está repetido en la clase {current}")
            elif t in owner:
                errors.append(f"classes.yml:{n}: el tipo de desvío {mostrar(t)} ya está en la clase {owner[t]} (un tipo va en una sola clase)")
            else:
                owner[t] = current
            seen.add(t)
    if not ids:
        errors.append("classes.yml: no tiene ninguna clase (`- id: <slug>`)")
    return ids, errors


def as_list(v):
    return v if isinstance(v, list) else [v]


def validate_rule(path, rel, classes):
    errs = []
    f, err = parse_frontmatter(path.read_text(encoding="utf-8"))
    if err:
        return [f"{rel}: {err}"]
    for k in REQUIRED:
        if k not in f:
            errs.append(f"{rel}: falta el campo {k}")
    for k in f:
        if k not in REQUIRED and k not in OPTIONAL:
            errs.append(f"{rel}: campo desconocido {k}")
    if errs:
        return errs
    if not SLUG.match(str(f["id"])):
        errs.append(f"{rel}: id {f['id']!r} no es un slug (minúsculas, números y guiones)")
    elif f["id"] != path.stem:
        errs.append(f"{rel}: id {f['id']!r} no coincide con el nombre del archivo")
    if f["status"] not in STATUS:
        errs.append(f"{rel}: status {f['status']!r} inválido (uno de {sorted(STATUS)})")
    if f["origin"] not in ORIGIN:
        errs.append(f"{rel}: origin {f['origin']!r} inválido (uno de {sorted(ORIGIN)})")
    if f["severity"] not in SEVERITY:
        errs.append(f"{rel}: severity {f['severity']!r} inválida (una de {sorted(SEVERITY)})")
    for k in ("applies_to", "scope"):
        vals = as_list(f[k])
        if not vals or any(not isinstance(x, str) or not (x == "*" or SLUG.match(x)) for x in vals):
            errs.append(f"{rel}: {k} tiene que ser \"*\" o una lista de slugs")
        elif "*" in vals and len(vals) > 1:
            errs.append(f"{rel}: {k} mezcla \"*\" con otros valores")
    if not isinstance(f["classes"], list):
        errs.append(f"{rel}: classes tiene que ser una lista (puede ser [])")
    else:
        for c in f["classes"]:
            if c not in classes:
                errs.append(f"{rel}: la clase {c!r} no existe en classes.yml")
    check = f.get("check")
    if "check" in f and (not isinstance(check, str) or not SLUG.match(check)):
        errs.append(f"{rel}: check tiene que ser el id (slug) de un check del kit")
    if "check" in f and not f.get("fail_message"):
        errs.append(f"{rel}: una regla con check necesita fail_message")
    if "fail_message" in f and "check" not in f:
        errs.append(f"{rel}: fail_message sin check")
    if f["severity"] == "block" and "check" not in f:
        errs.append(f"{rel}: severity block exige check (una regla de texto no puede bloquear)")
    if f["origin"] == "general" and not f["classes"] and "check" not in f:
        errs.append(f"{rel}: origin general solo con classes o check")
    if "accepted" in f:
        try:
            datetime.date.fromisoformat(str(f["accepted"]))
        except ValueError:
            errs.append(f"{rel}: accepted {f['accepted']!r} no es una fecha ISO (AAAA-MM-DD)")
    elif f["status"] == "accepted":
        errs.append(f"{rel}: una regla accepted necesita la fecha accepted")
    return errs


def tracked_files(root):
    """Archivos del repo: los de git (sin ignorados) si hay .git, y si no, todos los de la carpeta."""
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-co", "--exclude-standard"],
                             capture_output=True, text=True, check=True).stdout
        return sorted(p for p in out.split("\n") if p)
    except (OSError, subprocess.CalledProcessError):
        return sorted(str(p.relative_to(root)) for p in root.rglob("*")
                      if p.is_file() and ".git" not in p.relative_to(root).parts)


def validate_repo(root):
    errs = []
    for rel in tracked_files(root):
        if not (root / rel).is_file():
            continue
        if "/" not in rel:
            ok = rel in ALLOWED_ROOT or rel.endswith(".md")
        else:
            ok = rel.startswith(ALLOWED_DIRS)
        if not ok:
            errs.append(f"{rel}: archivo fuera de rules/, classes.yml, la documentación y las herramientas (los desvíos no entran a este repo, D5)")
        elif rel.startswith("rules/") and not (rel.endswith(".md") and rel.count("/") == 1):
            errs.append(f"{rel}: en rules/ solo van archivos <id>.md, sin subcarpetas")
    classes_path = root / "classes.yml"
    if not classes_path.is_file():
        return errs + ["classes.yml: no existe"]
    classes, e = load_classes(classes_path)
    errs += e
    for p in sorted((root / "rules").glob("*.md")) if (root / "rules").is_dir() else []:
        errs += validate_rule(p, f"rules/{p.name}", classes)
    return errs


def main(argv):
    if len(argv) > 2 or (len(argv) == 2 and argv[1] in ("-h", "--help")):
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 64
    root = Path(argv[1]) if len(argv) == 2 else Path(__file__).resolve().parent.parent
    if not root.is_dir():
        print(f"validate.py: {root} no es una carpeta", file=sys.stderr)
        return 64
    errs = validate_repo(root)
    for e in errs:
        print(e)
    if errs:
        print(f"{len(errs)} error(es).", file=sys.stderr)
        return 1
    print("Reglas OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
