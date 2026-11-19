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


def correr(files, timeout=None):
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for rel, txt in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(txt, encoding="utf-8")
        r = subprocess.run([sys.executable, str(VALIDATE), d], capture_output=True, text=True, timeout=timeout)
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


def dev(linea, despues_de="  description: x\n"):
    """El repo de base con `linea` debajo de la clase stale-docs (pegada a `despues_de`, con su salto de línea)."""
    assert despues_de in CLASES
    return base(**{"classes.yml": CLASES.replace(despues_de, despues_de + linea + "\n")})


class Validador(unittest.TestCase):
    def rechaza(self, files, texto):
        rc, out = correr(files)
        self.assertEqual(rc, 1, out)
        self.assertIn(texto, out)

    def rechaza_una(self, files, texto):
        """Como rechaza, y además es el único error: una equivocación, un mensaje."""
        rc, out = correr(files)
        self.assertEqual(rc, 1, out)
        self.assertIn(texto, out)
        self.assertIn("\n1 error(es).", out)

    def pasa(self, files):
        rc, out = correr(files)
        self.assertEqual(rc, 0, out)

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

    # La lista `deviations` de una clase (ADR-007 D5 del kit): los tipos de desvío que le corresponden.
    def test_deviations_valido_pasa(self):
        c = CLASES.replace("  description: x\n", "  description: x\n  deviations: [attribution, user-correction]\n")
        rc, out = correr(base(**{"classes.yml": c}))
        self.assertEqual(rc, 0, out)

    def test_deviation_no_es_slug(self):
        c = CLASES.replace("  description: x\n", "  description: x\n  deviations: [contract-*]\n")
        self.rechaza(base(**{"classes.yml": c}), "el tipo de desvío 'contract-*' no es un slug")

    def test_deviation_repetida_en_la_clase(self):
        c = CLASES.replace("  description: x\n", "  description: x\n  deviations: [attribution, attribution]\n")
        self.rechaza(base(**{"classes.yml": c}), "el tipo de desvío attribution está repetido en la clase stale-docs")

    def test_deviation_en_dos_clases(self):
        c = (CLASES.replace("  description: x\n", "  description: x\n  deviations: [attribution]\n")
             .replace("  description: y\n", "  description: y\n  deviations: [attribution]\n"))
        self.rechaza(base(**{"classes.yml": c}), "el tipo de desvío attribution ya está en la clase stale-docs")

    def test_deviations_no_es_lista(self):
        c = CLASES.replace("  description: x\n", "  description: x\n  deviations: attribution\n")
        self.rechaza(base(**{"classes.yml": c}), "deviations tiene que ser una lista en línea")

    def test_deviations_fuera_de_una_clase(self):
        self.rechaza(base(**{"classes.yml": "  deviations: [attribution]\n" + CLASES}), "deviations fuera de una clase")

    def test_deviations_dos_veces_en_la_clase(self):
        c = CLASES.replace("  description: x\n", "  description: x\n  deviations: [attribution]\n  deviations: [interrupt]\n")
        self.rechaza(base(**{"classes.yml": c}), "la clase stale-docs tiene dos listas deviations")

    # El criterio estricto del lector del kit (scripts/agents/check-docs.py), para que lo que pasa acá pase allá.
    INESPERADA = "línea inesperada con la clave deviations"
    EN_LINEA = "deviations tiene que ser una lista en línea"
    NO_SLUG = "no es un slug que empieza con una letra"

    def test_deviation_empieza_con_un_numero(self):
        for t in ("1st-try", "2fa-skip", "9"):
            with self.subTest(t):
                self.rechaza_una(dev(f"  deviations: [{t}]"), f"el tipo de desvío '{t}' {self.NO_SLUG}")

    def test_deviation_palabra_de_yaml(self):
        for t in ("y", "n", "yes", "no", "true", "false", "on", "off", "null"):
            with self.subTest(t):
                self.rechaza_una(dev(f"  deviations: [{t}]"), f"el tipo de desvío {t} es un booleano o null en YAML 1.1")

    def test_deviations_una_coma_de_mas(self):
        for lista in ("[attribution,]", "[attribution,,interrupt]", "[,attribution]", "[attribution, ]"):
            with self.subTest(lista):
                self.rechaza_una(dev(f"  deviations: {lista}"), "deviations de la clase stale-docs tiene un elemento vacío")

    def test_deviations_solo_comas(self):
        self.rechaza(dev("  deviations: [,]"), "deviations de la clase stale-docs tiene un elemento vacío")

    def test_deviations_un_solo_espacio_despues_de_los_dos_puntos(self):
        for linea in ("  deviations:[attribution]", "  deviations:  [attribution]", "  deviations:\t[attribution]",
                      "  deviations:\u00a0[attribution]"):
            with self.subTest(linea):
                self.rechaza_una(dev(linea), self.EN_LINEA)

    def test_deviations_otra_indentacion(self):
        for sangria in ("", " ", "   ", "    ", "\t", " \t", "\u00a0\u00a0"):
            with self.subTest(sangria):
                self.rechaza_una(dev(sangria + "deviations: [attribution]"), self.INESPERADA)

    def test_deviations_clave_mal_escrita(self):
        for clave in ("  Deviations:", "  DEVIATIONS:", "  deviations :", "- deviations:", "  - deviations:",
                      '  "deviations":', "  'deviations':", "  deviations", "  deviations=", " deviations", "deviations"):
            with self.subTest(clave):
                self.rechaza_una(dev(clave + " [attribution]"), self.INESPERADA)
        self.rechaza_una(dev("  deviations"), self.INESPERADA)

    def test_deviations_espacio_que_no_es_espacio_dentro_de_la_lista(self):
        for lista in ("[attribution\t]", "[\u00a0attribution]", "[attribution,\u3000interrupt]"):
            with self.subTest(lista):
                self.rechaza_una(dev(f"  deviations: {lista}"), self.NO_SLUG)

    def test_deviations_con_algo_despues_de_la_lista(self):
        for cola in (" # nota", " # nota]", " x", "\t", "\u00a0", "\u3000", "\x0c"):
            with self.subTest(cola):
                self.rechaza_una(dev("  deviations: [attribution]" + cola), self.EN_LINEA)

    def test_deviations_con_otro_corchete_adentro(self):
        for lista in ("[[attribution]]", "[attribution, [interrupt]]", "[attribution] [interrupt]"):
            with self.subTest(lista):
                self.rechaza_una(dev(f"  deviations: {lista}"), self.EN_LINEA)

    def test_deviations_con_un_comentario_adentro(self):
        for lista in ("[attribution # nota]", "[attribution, #interrupt]", "[#]"):
            with self.subTest(lista):
                self.rechaza_una(dev(f"  deviations: {lista}"), self.EN_LINEA)

    def test_deviations_detras_de_un_corte_que_no_es_salto_de_linea(self):
        # El lector del kit corta las líneas donde corta str.splitlines(): ve la lista como una línea aparte y la revisa.
        for corte in ("\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"):
            for lista in ("[1st-try]", "[attribution]"):
                with self.subTest(corte=corte, lista=lista):
                    c = CLASES.replace("  description: x\n", f"  description: x{corte}  deviations: {lista}\n")
                    self.rechaza_una(base(**{"classes.yml": c}), self.INESPERADA)

    def test_deviations_detras_de_un_retorno_de_carro_es_otra_linea(self):
        # Un \r suelto sí corta la línea, acá y en el kit (los dos leen el archivo en modo texto): la lista se revisa como tal.
        c = CLASES.replace("  description: x\n", "  description: x\r  deviations: [1st-try]\n")
        self.rechaza_una(base(**{"classes.yml": c}), f"classes.yml:3: el tipo de desvío '1st-try' {self.NO_SLUG}")
        self.pasa(base(**{"classes.yml": c.replace("1st-try", "attribution")}))

    def test_deviations_formas_validas_pasan(self):
        for linea in ("  deviations: []", "  deviations: [ ]", "  deviations: [attribution,interrupt]",
                      "  deviations: [ attribution , interrupt ]", "  deviations: [attribution]   ", "  deviations: [a1-b2, x, yes-no]"):
            with self.subTest(linea):
                self.pasa(dev(linea))

    def test_deviations_antes_de_la_descripcion_pasa(self):
        self.pasa(dev("  deviations: [attribution]", despues_de="- id: stale-docs\n"))

    def test_deviations_con_crlf_pasa(self):
        files = dev("  deviations: [attribution, interrupt]")
        files["classes.yml"] = files["classes.yml"].replace("\n", "\r\n")
        self.pasa(files)

    def test_deviations_en_un_comentario_o_en_una_descripcion_no_es_una_lista(self):
        for linea in ("  # deviations: [1st-try]", "# deviations:[1st-try]", "  description: counts deviations:[1st-try] twice"):
            with self.subTest(linea):
                self.pasa(dev(linea, despues_de="- id: stale-docs\n"))

    def test_deviation_larguisima_se_corta_en_el_mensaje(self):
        largo = "a" * 5000
        otra = CLASES.replace("  description: y\n", f"  description: y\n  deviations: [{largo}]\n")
        casos = {
            "no es slug": (dev(f"  deviations: [{largo}*]"), self.NO_SLUG),
            "repetida": (dev(f"  deviations: [{largo}, {largo}]"), "está repetido en la clase stale-docs"),
            "en dos clases": ({**base(), "classes.yml": otra.replace("  description: x\n", f"  description: x\n  deviations: [{largo}]\n")},
                              "ya está en la clase stale-docs"),
        }
        for nombre, (files, texto) in casos.items():
            with self.subTest(nombre):
                rc, out = correr(files)
                self.assertEqual(rc, 1, out[:300])
                self.assertIn(texto, out)
                self.assertLess(max(len(l) for l in out.split("\n")), 300)

    def test_deviation_con_caracter_de_control_no_se_imprime_tal_cual(self):
        rc, out = correr(dev("  deviations: [\x1b[31mrojo\x07]"))
        self.assertEqual(rc, 1, out)
        self.assertNotIn("\x1b", out)
        self.assertNotIn("\x07", out)
        rc, out = correr(dev("  deviations: [att\x1bribution\u202e]"))
        self.assertEqual(rc, 1, out)
        self.assertIn(self.NO_SLUG, out)
        self.assertNotIn("\x1b", out)
        self.assertNotIn("\u202e", out)

    def test_lineas_hostiles_no_cuelgan(self):
        n = 200000
        for nombre, linea in (("cortes", "\x0c" * n), ("cortes unicode", "\u2028" * n), ("espacios tras la clave", "  deviations:" + " " * n),
                              ("espacios antes de la clave", " " * n + "deviations"), ("guiones", "- " * n + "deviations:"),
                              ("comas", "  deviations: [" + "," * n + "x"), ("tipo largo", "  deviations: [" + "a-" * n + "]"),
                              ("corchetes", "  deviations: " + "[" * n), ("claves", "\x0cdeviations" * (n // 10))):
            with self.subTest(nombre):
                rc, out = correr(dev(linea), timeout=20)
                self.assertIn(rc, (0, 1), out[:300])
                self.assertNotIn("Traceback", out)

    def test_el_repo_real_valida(self):
        r = subprocess.run([sys.executable, str(VALIDATE), str(RAIZ)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
