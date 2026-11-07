"""Tests del validador (scripts/validate.py). Cada caso inválido tiene que fallar por lo que dice."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VALIDATE = RAIZ / "scripts" / "validate.py"

CLASES = "- id: stale-docs\n  description: x\n- id: uncovered-case\n  description: y\n"
REGLA = """---
id: mi-regla
status: accepted
origin: observed
applies_to: [implementer]
scope: "*"
classes: [stale-docs]
severity: fix
accepted: 2026-11-04
---
Una línea con la regla.
"""


def correr(files):
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for rel, txt in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(txt, encoding="utf-8")
        r = subprocess.run([sys.executable, str(VALIDATE), d], capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr


def con(**cambios):
    """REGLA con campos cambiados (None borra la línea del campo)."""
    out = []
    for line in REGLA.split("\n"):
        k = line.split(":")[0]
        if k in cambios:
            if cambios[k] is not None:
                out.append(f"{k}: {cambios[k]}")
        else:
            out.append(line)
    return "\n".join(out)


def base(regla=REGLA, nombre="rules/mi-regla.md", **extra):
    return {"classes.yml": CLASES, nombre: regla, **extra}


class Validador(unittest.TestCase):
    def rechaza(self, files, texto):
        rc, out = correr(files)
        self.assertEqual(rc, 1, out)
        self.assertIn(texto, out)

    def test_regla_valida_pasa(self):
        rc, out = correr(base())
        self.assertEqual(rc, 0, out)

    def test_falta_un_campo(self):
        self.rechaza(base(con(severity=None)), "falta el campo severity")

    def test_status_invalido(self):
        self.rechaza(base(con(status="aceptada")), "status 'aceptada' inválido")

    def test_origin_invalido(self):
        self.rechaza(base(con(origin="inventada")), "origin 'inventada' inválido")

    def test_severity_invalida(self):
        self.rechaza(base(con(severity="grave")), "severity 'grave' inválida")

    def test_campo_desconocido(self):
        self.rechaza(base(REGLA.replace("severity: fix", "severity: fix\nextra: 1")), "campo desconocido extra")

    def test_id_distinto_del_archivo(self):
        self.rechaza(base(con(id="otra")), "no coincide con el nombre del archivo")

    def test_id_no_es_slug(self):
        self.rechaza(base(con(id="Mi_Regla"), nombre="rules/Mi_Regla.md"), "no es un slug")

    def test_clase_inexistente(self):
        self.rechaza(base(con(classes="[no-existe]")), "la clase 'no-existe' no existe en classes.yml")

    def test_block_sin_check(self):
        self.rechaza(base(con(severity="block")), "severity block exige check")

    def test_block_con_check_pasa(self):
        r = con(severity="block").replace("severity: block", "severity: block\ncheck: pr-metadata\nfail_message: \"el PR miente\"")
        rc, out = correr(base(r))
        self.assertEqual(rc, 0, out)

    def test_check_sin_fail_message(self):
        r = con().replace("severity: fix", "severity: fix\ncheck: pr-metadata")
        self.rechaza(base(r), "necesita fail_message")

    def test_general_sin_classes_ni_check(self):
        self.rechaza(base(con(origin="general", classes="[]")), "origin general solo con classes o check")

    def test_general_con_classes_pasa(self):
        rc, out = correr(base(con(origin="general")))
        self.assertEqual(rc, 0, out)

    def test_accepted_sin_fecha(self):
        self.rechaza(base(con(accepted=None)), "necesita la fecha accepted")

    def test_fecha_no_iso(self):
        self.rechaza(base(con(accepted="04/11/2026")), "no es una fecha ISO")

    def test_deprecated_sin_fecha_pasa(self):
        rc, out = correr(base(con(status="deprecated", accepted=None)))
        self.assertEqual(rc, 0, out)

    def test_scope_mezcla_asterisco(self):
        self.rechaza(base(con(scope='["*", barrilete-kit]')), "mezcla")

    def test_sin_frontmatter(self):
        self.rechaza(base("sin frontmatter\n"), "no empieza con el frontmatter")

    def test_frontmatter_sin_cerrar(self):
        self.rechaza(base(REGLA.replace("accepted: 2026-11-04\n---\nUna línea con la regla.\n", "accepted: 2026-11-04\n")), "no cierra")

    def test_archivo_fuera_de_lo_permitido(self):
        self.rechaza(base(**{"desvios.jsonl": "{}\n"}), "archivo fuera de rules/")

    def test_checks_ya_no_se_permite(self):
        self.rechaza(base(**{"checks/pr-metadata.sh": "#!/bin/sh\n"}), "checks/pr-metadata.sh: archivo fuera de")

    def test_subcarpeta_en_rules(self):
        self.rechaza(base(**{"rules/sub/otra.md": REGLA}), "sin subcarpetas")

    def test_docs_y_herramientas_pasan(self):
        rc, out = correr(base(**{"README.md": "# x\n", "docs/guia.md": "x\n", "scripts/validate.py": "x\n"}))
        self.assertEqual(rc, 0, out)

    def test_sin_classes_yml(self):
        self.rechaza({"rules/mi-regla.md": REGLA}, "classes.yml: no existe")

    def test_classes_yml_sin_clases(self):
        self.rechaza({"classes.yml": "# vacío\n", "rules/mi-regla.md": REGLA}, "no tiene ninguna clase")

    def test_clase_repetida(self):
        self.rechaza(base(**{"classes.yml": CLASES + "- id: stale-docs\n"}), "está repetida")

    def test_el_repo_real_valida(self):
        r = subprocess.run([sys.executable, str(VALIDATE), str(RAIZ)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
