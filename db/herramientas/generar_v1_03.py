"""Genera migration/V1_03__cargar_referencia_ambiental.sql desde referencia/ambiental_2026.json.

Uso (desde la carpeta bd):
    python3 -I herramientas/generar_v1_03.py referencia/ambiental_2026.json migration/V1_03__cargar_referencia_ambiental.sql

Reglas:
- Salida determinista: el mismo JSON produce el mismo archivo byte a byte (orden fijo, sin fechas),
  así el checksum de Flyway no cambia. Las pruebas regeneran el archivo y lo comparan con diff.
- Cuando Flyway ya aplicó V1_03 en una base compartida, el archivo no se regenera encima;
  una corrección va en una migración nueva o en una versión de catálogo nueva.
- El JSON solo trae datos curriculares (SO, PI, rúbrica, competencias, asignaturas), sin datos personales.
- Normaliza: PI desde el texto «SO.n» (nunca desde el valor float del Excel), quita el prefijo «1.1 » de
  la descripción del PI, recorta los espacios del borde de códigos, textos de SO y nombres («E1 » pasa a E1), instrumento «-» pasa a NULL,
  estadío Inicial/Refuerzo/Logrado pasa a INICIAL/REFUERZO/LOGRADO y tipo Genérica/Específica a GENERICA/ESPECIFICA.
- Depura el nombre de la asignatura (H23), que llega a la columna CURSO de Power BI: junta los espacios repetidos
  y pasa a minúscula los artículos, preposiciones y conjunciones que no abren el nombre
  («Formulación Y Evaluación  De Proyectos Sostenibles» pasa a «Formulación y Evaluación de Proyectos Sostenibles»).
  El JSON se conserva tal como sale de la fuente.
- Falla (código de salida 1) ante duplicados, códigos fuera de formato o fuentes que no coinciden, antes de escribir.
"""
import hashlib
import json
import re
import sys

CATALOGO = "AMB-2026"
CARRERA = "AMB"
FACULTAD = ("FI", "Facultad de Ingeniería")
PERIODOS = [(2025, 1), (2025, 2), (2026, 1), (2026, 2)]
ESTADIO = {"Inicial": "INICIAL", "Refuerzo": "REFUERZO", "Logrado": "LOGRADO"}
ESTADIO_LETRA = {"I": "INICIAL", "R": "REFUERZO", "L": "LOGRADO"}
TIPO = {"Genérica": "GENERICA", "Específica": "ESPECIFICA"}
MINUSCULA = {"a", "al", "con", "de", "del", "e", "el", "en", "la", "las", "los", "o", "para", "por", "u", "y"}


def falla(msg):
    sys.stderr.write("ERROR: " + msg + "\n")
    sys.exit(1)


def q(v):
    """Literal SQL con comillas simples duplicadas; NULL para None."""
    if v is None:
        return "NULL"
    if isinstance(v, int):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def nombre_asignatura(texto):
    """Nombre depurado: espacios simples y conectores en minúscula salvo al inicio."""
    palabras = texto.split()
    return " ".join(w if i == 0 or w.lower() not in MINUSCULA else w.lower() for i, w in enumerate(palabras))


def valores(filas):
    return ",\n".join(" (" + ", ".join(q(x) for x in f) + ")" for f in filas)


def main(ruta_json, ruta_sql):
    crudo = open(ruta_json, "rb").read()
    huella = hashlib.sha256(crudo).hexdigest()
    d = json.loads(crudo.decode("utf-8"))

    # SO
    so = sorted((int(s["numero"]), s["descripcion"].strip()) for s in d["so"])
    if len({n for n, _ in so}) != len(so):
        falla("SO duplicado")
    so_nums = {n for n, _ in so}

    # PI con su rúbrica
    pis, rubrica = [], []
    for p in d["pi"]:
        cod = str(p["codigo"]).strip()
        m = re.fullmatch(r"([1-9][0-9]?)\.([1-9][0-9]?)", cod)
        if not m or int(m.group(1)) != int(p["so"]) or int(m.group(1)) not in so_nums:
            falla(f"PI mal formado o con SO distinto: {cod}")
        desc = re.sub(r"^\s*" + re.escape(cod) + r"\s*", "", p["descripcion"]).strip()
        pis.append((int(m.group(1)), int(m.group(2)), cod, desc))
        for nivel, texto in sorted(p["niveles"].items(), key=lambda kv: int(kv[0])):
            if texto is not None and str(texto).strip():
                if int(nivel) not in (-1, 1, 2, 3, 4, 5):
                    falla(f"nivel de rúbrica fuera de lista en {cod}: {nivel}")
                rubrica.append((cod, int(nivel), str(texto).strip()))
    pis.sort()
    if len({c for _, _, c, _ in pis}) != len(pis):
        falla("PI duplicado")

    # Asignaturas: unión de las dos fuentes con código; nombre y ciclo deben coincidir
    asig = {}
    for x in d["asignatura_so"] + d["asignatura_competencia_nivel"]:
        c = str(x["codigo"]).strip()
        if not re.fullmatch(r"[0-9]{4}([0-9]{2})?", c):
            falla(f"código de asignatura inválido: {c}")
        par = (nombre_asignatura(x["asignatura"]), int(x["nivel"]))
        if asig.setdefault(c, par) != par:
            falla(f"asignatura {c} con nombre o ciclo distintos entre fuentes")
    nombres = {}
    for c, (n, _) in asig.items():
        if nombres.setdefault(n, c) != c:
            falla(f"asignatura {n} con dos códigos")

    # Instrumentos y asignatura-SO
    asig_so, inst = [], set()
    for x in d["asignatura_so"]:
        i = (x["instrumento"] or "").strip()
        i = None if i in ("", "-") else i
        if i:
            inst.add(i)
        if int(x["so"]) not in so_nums:
            falla(f"asignatura {x['codigo']} con SO inexistente {x['so']}")
        asig_so.append((str(x["codigo"]).strip(), int(x["so"]), i))
    asig_so.sort(key=lambda t: (t[0], t[1]))
    if len({(a, s) for a, s, _ in asig_so}) != len(asig_so):
        falla("par asignatura-SO duplicado")

    # Competencias y su SO
    comp = []
    for x in d["competencias"]:
        c = str(x["codigo"]).strip()
        if not re.fullmatch(r"[GE][1-9][0-9]?", c):
            falla(f"código de competencia inválido: {c!r}")
        tipo = TIPO[x["tipo"]]
        if tipo[0] != c[0]:
            falla(f"tipo de competencia incoherente: {c}")
        comp.append((c, x["nombre"].strip(), tipo, None if x["so"] is None else int(x["so"])))
    comp.sort(key=lambda t: (t[0][0] != "G", int(t[0][1:])))
    comp_codigos = {c for c, _, _, _ in comp}
    if len(comp_codigos) != len(comp):
        falla("competencia duplicada")

    # Asignatura-competencia con estadío; se contrasta con la hoja «Cursos»
    asig_comp = []
    for x in d["asignatura_competencia_nivel"]:
        c, k = str(x["codigo"]).strip(), str(x["competencia"]).strip()
        if k not in comp_codigos:
            falla(f"competencia desconocida {k!r} en {c}")
        asig_comp.append((c, k, ESTADIO[x["estadio"].strip()]))
    asig_comp.sort(key=lambda t: (t[0], t[1][0] != "G", int(t[1][1:])))
    if len({(a, k) for a, k, _ in asig_comp}) != len(asig_comp):
        falla("par asignatura-competencia duplicado")
    por_nombre = {(asig[a][0], k, e) for a, k, e in asig_comp}
    cursos = {(nombre_asignatura(x["asignatura"]), str(x["competencia"]).strip(), ESTADIO_LETRA[x["estadio"]])
              for x in d["asignatura_competencia_cursos"]}
    if por_nombre != cursos:
        falla("la hoja Cursos y Base cursos - Nivel no coinciden en asignatura, competencia y estadío")

    conteos = {
        "so": len(so), "pi": len(pis), "rubrica_nivel": len(rubrica), "competencia": len(comp),
        "competencia_so": sum(1 for x in comp if x[3] is not None), "asignatura": len(asig),
        "plan_estudios": len(asig), "asignatura_so": len(asig_so),
        "asignatura_competencia": len(asig_comp), "instrumento": len(inst),
    }
    ref = d.get("conteos", {})
    for k_json, k in (("so", "so"), ("pi", "pi"), ("competencias", "competencia"),
                      ("asignatura_so", "asignatura_so"), ("asignatura_competencia_nivel", "asignatura_competencia"),
                      ("asignaturas_union", "asignatura")):
        if k_json in ref and ref[k_json] != conteos[k]:
            falla(f"conteo de {k} ({conteos[k]}) distinto del declarado en el JSON ({ref[k_json]})")

    cv = (f"JOIN abet.catalogo_version cv ON cv.codigo = {q(CATALOGO)}")
    L = [
        "-- V1_03  Datos de referencia curriculares de Ingeniería Ambiental (solo datos).",
        "-- GENERADO por herramientas/generar_v1_03.py desde referencia/ambiental_2026.json; no se edita a mano.",
        f"-- SHA-256 del JSON de referencia: {huella}",
        "-- Cubre H02 (facultad y carrera), H23 (códigos únicos y depurados), H21 y C6 (PI como texto SO.número),",
        "-- C8 (ciclo de malla), H26 (todo cuelga de la versión de catálogo AMB-2026, en BORRADOR) y H35 (instrumentos).",
        "",
        f"INSERT INTO abet.facultad (codigo, nombre) VALUES ({q(FACULTAD[0])}, {q(FACULTAD[1])});",
        "",
        "INSERT INTO abet.carrera (facultad_id, codigo, nombre)",
        f"SELECT facultad_id, {q(CARRERA)}, {q(d['carrera'])} FROM abet.facultad WHERE codigo = {q(FACULTAD[0])};",
        "",
        "INSERT INTO abet.periodo (anio, ciclo, codigo) VALUES",
        valores([(a, c, f"{a}-{c}") for a, c in PERIODOS]) + ";",
        "",
        "INSERT INTO abet.catalogo_version (carrera_id, codigo, estado, huella_fuente)",
        f"SELECT carrera_id, {q(CATALOGO)}, 'BORRADOR', {q(huella)} FROM abet.carrera WHERE codigo = {q(CARRERA)};",
        "",
        "INSERT INTO abet.asignatura (codigo, nombre) VALUES",
        valores([(c, n) for c, (n, _) in sorted(asig.items())]) + ";",
        "",
        "INSERT INTO abet.plan_estudios (catalogo_version_id, asignatura_id, ciclo_malla)",
        "SELECT cv.catalogo_version_id, a.asignatura_id, v.ciclo_malla FROM (VALUES",
        valores([(c, ciclo) for c, (_, ciclo) in sorted(asig.items())]),
        ") AS v (codigo, ciclo_malla)",
        "JOIN abet.asignatura a ON a.codigo = v.codigo",
        cv + ";",
        "",
        "INSERT INTO abet.so (catalogo_version_id, numero, descripcion)",
        "SELECT cv.catalogo_version_id, v.numero, v.descripcion FROM (VALUES",
        valores(so),
        ") AS v (numero, descripcion)",
        cv + ";",
        "",
        "INSERT INTO abet.pi (catalogo_version_id, so_id, so_numero, numero, codigo, descripcion)",
        "SELECT cv.catalogo_version_id, s.so_id, s.numero, v.numero, v.codigo, v.descripcion FROM (VALUES",
        valores(pis),
        ") AS v (so_numero, numero, codigo, descripcion)",
        cv,
        "JOIN abet.so s ON s.catalogo_version_id = cv.catalogo_version_id AND s.numero = v.so_numero;",
        "",
        "INSERT INTO abet.rubrica_nivel (pi_id, nivel, descriptor)",
        "SELECT p.pi_id, v.nivel, v.descriptor FROM (VALUES",
        valores(rubrica),
        ") AS v (pi_codigo, nivel, descriptor)",
        cv,
        "JOIN abet.pi p ON p.catalogo_version_id = cv.catalogo_version_id AND p.codigo = v.pi_codigo;",
        "",
        "INSERT INTO abet.instrumento (catalogo_version_id, nombre)",
        "SELECT cv.catalogo_version_id, v.nombre FROM (VALUES",
        valores([(i,) for i in sorted(inst)]),
        ") AS v (nombre)",
        cv + ";",
        "",
        "INSERT INTO abet.asignatura_so (catalogo_version_id, asignatura_id, so_id, instrumento_id)",
        "SELECT cv.catalogo_version_id, a.asignatura_id, s.so_id, i.instrumento_id FROM (VALUES",
        valores(asig_so),
        ") AS v (codigo, so_numero, instrumento)",
        cv,
        "JOIN abet.asignatura a ON a.codigo = v.codigo",
        "JOIN abet.so s ON s.catalogo_version_id = cv.catalogo_version_id AND s.numero = v.so_numero",
        "LEFT JOIN abet.instrumento i ON i.catalogo_version_id = cv.catalogo_version_id AND i.nombre = v.instrumento;",
        "",
        "INSERT INTO abet.competencia (catalogo_version_id, codigo, nombre, tipo)",
        "SELECT cv.catalogo_version_id, v.codigo, v.nombre, v.tipo FROM (VALUES",
        valores([(c, n, t) for c, n, t, _ in comp]),
        ") AS v (codigo, nombre, tipo)",
        cv + ";",
        "",
        "-- G1, G2, G5 y G7 no aportan a ningún SO y no tienen fila.",
        "INSERT INTO abet.competencia_so (catalogo_version_id, competencia_id, so_id)",
        "SELECT cv.catalogo_version_id, k.competencia_id, s.so_id FROM (VALUES",
        valores([(c, s) for c, _, _, s in comp if s is not None]),
        ") AS v (codigo, so_numero)",
        cv,
        "JOIN abet.competencia k ON k.catalogo_version_id = cv.catalogo_version_id AND k.codigo = v.codigo",
        "JOIN abet.so s ON s.catalogo_version_id = cv.catalogo_version_id AND s.numero = v.so_numero;",
        "",
        "INSERT INTO abet.asignatura_competencia (catalogo_version_id, asignatura_id, competencia_id, estadio)",
        "SELECT cv.catalogo_version_id, a.asignatura_id, k.competencia_id, v.estadio FROM (VALUES",
        valores(asig_comp),
        ") AS v (codigo, competencia, estadio)",
        cv,
        "JOIN abet.asignatura a ON a.codigo = v.codigo",
        "JOIN abet.competencia k ON k.catalogo_version_id = cv.catalogo_version_id AND k.codigo = v.competencia;",
        "",
        "-- Aserción de carga: la migración falla si algún conteo no coincide con el JSON.",
        "-- Es la única excepción a «sin plpgsql» de la entrega 1; en T-SQL se traduce a IF ... THROW.",
        "DO $$",
        "DECLARE",
        "    v_version smallint;",
        "    v_n       bigint;",
        "BEGIN",
        f"    SELECT catalogo_version_id INTO v_version FROM abet.catalogo_version WHERE codigo = {q(CATALOGO)};",
    ]
    chequeos = [
        ("so", "SELECT count(*) FROM abet.so WHERE catalogo_version_id = v_version"),
        ("pi", "SELECT count(*) FROM abet.pi WHERE catalogo_version_id = v_version"),
        ("rubrica_nivel", "SELECT count(*) FROM abet.rubrica_nivel r JOIN abet.pi p ON p.pi_id = r.pi_id "
                          "WHERE p.catalogo_version_id = v_version"),
        ("competencia", "SELECT count(*) FROM abet.competencia WHERE catalogo_version_id = v_version"),
        ("competencia_so", "SELECT count(*) FROM abet.competencia_so WHERE catalogo_version_id = v_version"),
        ("asignatura", "SELECT count(*) FROM abet.asignatura"),
        ("plan_estudios", "SELECT count(*) FROM abet.plan_estudios WHERE catalogo_version_id = v_version"),
        ("asignatura_so", "SELECT count(*) FROM abet.asignatura_so WHERE catalogo_version_id = v_version"),
        ("asignatura_competencia", "SELECT count(*) FROM abet.asignatura_competencia WHERE catalogo_version_id = v_version"),
        ("instrumento", "SELECT count(*) FROM abet.instrumento WHERE catalogo_version_id = v_version"),
    ]
    for tabla, sql in chequeos:
        L += [f"    {sql} INTO v_n;",
              f"    IF v_n <> {conteos[tabla]} THEN",
              f"        RAISE EXCEPTION 'abet.{tabla}: se esperaban {conteos[tabla]} filas y hay %', v_n;",
              "    END IF;"]
    L += ["END;", "$$;", ""]
    with open(ruta_sql, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        falla("uso: generar_v1_03.py <referencia.json> <salida.sql>")
    main(sys.argv[1], sys.argv[2])
