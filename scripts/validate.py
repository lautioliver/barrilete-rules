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


def load_classes(path):
    """Ids de classes.yml: líneas `- id: <slug>`. Devuelve (ids, errores)."""
    ids, errors = set(), []
    for n, line in enumerate(path.read_text(encoding="utf-8").split("\n"), start=1):
        m = re.match(r"^- id:\s*(\S+)\s*$", line)
        if m:
            if not SLUG.match(m.group(1)):
                errors.append(f"classes.yml:{n}: la clase {m.group(1)!r} no es un slug")
            if m.group(1) in ids:
                errors.append(f"classes.yml:{n}: la clase {m.group(1)} está repetida")
            ids.add(m.group(1))
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
