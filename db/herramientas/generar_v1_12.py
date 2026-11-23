"""Genera migration/V1_12__cargar_referencia_industrial.sql desde referencia/industrial_2026.json (T020, spec 008).

Uso, desde la carpeta db.
    python3 -I herramientas/generar_v1_12.py referencia/industrial_2026.json migration/V1_12__cargar_referencia_industrial.sql

Reglas.
- Salida determinista, como generar_v1_03.py. El mismo JSON produce el mismo archivo byte a byte (orden fijo, sin
  fechas), así el checksum de Flyway no cambia, y db/pruebas/correr_pruebas.sh regenera el archivo y lo compara.
- Cuando Flyway ya aplicó V1_12 en una base compartida, el archivo no se regenera encima. Una corrección va en una
  migración nueva o en una versión de catálogo nueva.
- El JSON solo trae datos curriculares de la hoja «Información por Asignatura» de un R-17 de profesor (7 SO, 21 PI,
  64 pares de asignatura y PI y 53 asignaturas), sin datos de personas. No trae rúbricas, competencias ni estadíos, así
  que IND-2026 queda en BORRADOR sin filas en abet.rubrica_nivel hasta D-50.
- Una asignatura que ya registra V1_03 se reutiliza con su código y su nombre, sin escribirla otra vez. Su nombre en la
  referencia, escrito en mayúsculas, se compara con el de V1_03 sin distinguir mayúsculas y con las tildes, así
  «QUÍMICA GENERAL» es «Química General» y «Quimica general» no lo es. EQUIVALENCIAS lista los dos nombres que la hoja
  escribe con otras palabras (cambio del 2026-11-23 en la construcción de la spec 008).
- El nombre de una asignatura nueva pasa de mayúsculas a la forma de V1_03, con la inicial de cada palabra en mayúscula,
  los conectores en minúscula salvo al inicio y los números romanos en mayúscula («INVESTIGACIÓN DE OPERACIONES II» pasa
  a «Investigación de Operaciones II»). El JSON se conserva tal como sale de la fuente.
- inconsistencias_de_la_fuente lista una asignatura que la hoja escribe de dos formas, y V1_12 usa la primera. Toda otra
  diferencia de nombre o de ciclo de una asignatura dentro de la referencia detiene el generador.
- El par asignatura y SO sale de los pares de asignatura y PI. El único instrumento es el «Portafolio 3» de 5643 y SO 6,
  el hecho que verificó la Oficina de Calidad el 2026-11-23, porque la hoja no trae instrumentos. Los demás pares
  quedan sin instrumento.
- Falla (código de salida 1) antes de escribir ante un SO o un PI mal formado o repetido, el SO de un PI que no existe,
  una descripción de PI de más de 300 caracteres, un código de asignatura que no tiene 4 ni 6 dígitos, un ciclo de
  malla fuera de 1 a 12, un nombre distinto del ya registrado en V1_03 o un conteo distinto del que declara el JSON.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

CATALOGO = "IND-2026"
CARRERA = "IND"
FACULTAD = "FI"
V1_03 = Path(__file__).resolve().parents[1] / "migration" / "V1_03__cargar_referencia_ambiental.sql"
# Nombres de la hoja que dicen con otras palabras la misma asignatura que V1_03 (cambio del 2026-11-23).
EQUIVALENCIAS = {"560044": "FUNDAMENTOS DE LA PROGRAMACIÓN", "6508": "METODOLOGÍA DE INVESTIGACIÓN"}
# Instrumento de cada par asignatura y SO que verificó la Oficina de Calidad (spec 008, sesión del 2026-11-23).
INSTRUMENTOS = {("5643", 6): "Portafolio 3"}
# Los mismos conectores de generar_v1_03.py, que python -I no deja importar desde esta carpeta.
MINUSCULA = {"a", "al", "con", "de", "del", "e", "el", "en", "la", "las", "los", "o", "para", "por", "u", "y"}
ROMANO = re.compile(r"[IVX]+")
LARGO_PI = 300


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


def valores(filas):
    return ",\n".join(" (" + ", ".join(q(x) for x in f) + ")" for f in filas)


def nombre_asignatura(texto):
    """Nombre de una asignatura nueva en la forma de V1_03, desde las mayúsculas de la hoja."""
    palabras = []
    for i, w in enumerate(texto.split()):
        if ROMANO.fullmatch(w):
            palabras.append(w)
        elif i > 0 and w.lower() in MINUSCULA:
            palabras.append(w.lower())
        else:
            palabras.append("/".join(p[:1].upper() + p[1:].lower() for p in w.split("/")))
    return " ".join(palabras)


def registradas(ruta=V1_03):
    """Código y nombre de cada asignatura que V1_03 inserta en abet.asignatura."""
    texto = ruta.read_text(encoding="utf-8")
    bloque = texto.split("INSERT INTO abet.asignatura (codigo, nombre) VALUES", 1)[1].split(";", 1)[0]
    return {c: n.replace("''", "'") for c, n in re.findall(r"\('([0-9]{4,6})', '((?:[^']|'')*)'\)", bloque)}


def entero(valor):
    """Entero de un número del JSON; None para un texto, un booleano o un valor ausente."""
    return valor if isinstance(valor, int) and not isinstance(valor, bool) else None


def main(ruta_json, ruta_sql):
    crudo = open(ruta_json, "rb").read()
    huella = hashlib.sha256(crudo).hexdigest()
    d = json.loads(crudo.decode("utf-8"))

    # SO
    so = []
    for s in d["so"]:
        n = entero(s.get("numero"))
        if n is None or not 1 <= n <= 20 or not str(s.get("descripcion") or "").strip():
            falla(f"SO mal formado: {s.get('numero')!r}")
        so.append((n, s["descripcion"].strip()))
    so.sort()
    if len({n for n, _ in so}) != len(so):
        falla("SO repetido")
    so_nums = {n for n, _ in so}

    # PI
    pis = []
    for p in d["pi"]:
        cod = str(p.get("codigo") or "").strip()
        m = re.fullmatch(r"([1-9][0-9]?)\.([1-9][0-9]?)", cod)
        if not m or entero(p.get("so")) != int(m.group(1)):
            falla(f"PI mal formado o con SO distinto de su código: {cod!r}")
        if int(m.group(1)) not in so_nums:
            falla(f"el SO del PI {cod} no está en la referencia")
        desc = re.sub(r"^\s*" + re.escape(cod) + r"\s+", "", str(p.get("descripcion") or "")).strip()
        if not desc:
            falla(f"el PI {cod} no trae descripción")
        if len(desc) > LARGO_PI:
            falla(f"el largo de la descripción del PI {cod} pasa de {LARGO_PI} caracteres ({len(desc)})")
        pis.append((int(m.group(1)), int(m.group(2)), cod, desc))
    codigos_pi = [c for _, _, c, _ in pis]
    for cod in sorted(set(codigos_pi)):
        if codigos_pi.count(cod) > 1:
            falla(f"el PI repetido {cod} aparece {codigos_pi.count(cod)} veces")
    pis.sort()
    so_de_pi = {c: s for s, _, c, _ in pis}

    # Asignaturas desde los pares asignatura y PI
    otra_forma = {}
    for x in d.get("inconsistencias_de_la_fuente", []):
        primera, otra = tuple(x["primera"]), tuple(x["otra"])
        otra_forma[(str(x["codigo"]), otra[0], otra[1])] = primera
    asig, pares = {}, []
    for x in d["asignatura_pi"]:
        c = str(x.get("codigo") or "").strip()
        if not re.fullmatch(r"[0-9]{4}([0-9]{2})?", c):
            falla(f"el código de la asignatura {c!r} no tiene 4 ni 6 dígitos")
        nivel = entero(x.get("nivel"))
        if nivel is None or not 1 <= nivel <= 12:
            falla(f"el ciclo de malla de la asignatura {c} falta o no está entre 1 y 12")
        nombre = " ".join(str(x.get("asignatura") or "").split())
        par = otra_forma.get((c, nombre, nivel), (nombre, nivel))
        if asig.setdefault(c, par) != par:
            falla(f"la asignatura {c} trae nombres o ciclos distintos dentro de la referencia")
        pi = str(x.get("pi") or "").strip()
        if pi not in so_de_pi:
            falla(f"el PI {pi!r} de la asignatura {c} no está en la referencia")
        pares.append((c, pi))
    if len(set(pares)) != len(pares):
        falla("par asignatura-PI repetido")
    for (c, nombre, nivel), primera in otra_forma.items():
        if asig.get(c) != primera:
            falla(f"la inconsistencia declarada de {c} no coincide con la referencia")

    # Asignaturas que V1_03 ya registra: mismo nombre salvo mayúsculas, o el de EQUIVALENCIAS
    ya = registradas()
    nuevas = {}
    for c, (nombre, nivel) in sorted(asig.items()):
        if c in ya:
            if nombre.casefold() != ya[c].casefold() and EQUIVALENCIAS.get(c) != nombre:
                falla(f"la asignatura {c} trae el nombre distinto del ya registrado en V1_03")
        else:
            nuevas[c] = nombre_asignatura(nombre)

    # Pares asignatura y SO con su instrumento
    asig_so = sorted({(c, so_de_pi[pi]) for c, pi in pares})
    for par in INSTRUMENTOS:
        if par not in asig_so:
            falla(f"el par {par[0]} y SO {par[1]} del instrumento {INSTRUMENTOS[par]} no está en la referencia")
    asig_so = [(c, s, INSTRUMENTOS.get((c, s))) for c, s in asig_so]
    inst = sorted(set(INSTRUMENTOS.values()))

    conteos = {"so": len(so), "pi": len(pis), "rubrica_nivel": 0, "competencia": 0, "plan_estudios": len(asig),
               "asignatura_so": len(asig_so), "asignatura_competencia": 0, "instrumento": len(inst)}
    ref = d.get("conteos", {})
    for k_json, valor in (("so", len(so)), ("pi", len(pis)), ("asignatura_pi", len(pares)),
                          ("asignaturas", len(asig))):
        if k_json in ref and ref[k_json] != valor:
            falla(f"conteo de {k_json} ({valor}) distinto del declarado en el JSON ({ref[k_json]})")

    cv = f"JOIN abet.catalogo_version cv ON cv.codigo = {q(CATALOGO)}"
    L = [
        "-- V1_12  Datos de referencia curriculares de Ingeniería Industrial (solo datos, spec 008, US-67).",
        "-- GENERADO por herramientas/generar_v1_12.py desde referencia/industrial_2026.json; no se edita a mano.",
        f"-- SHA-256 del JSON de referencia: {huella}",
        "-- Carga la carrera IND, el catálogo IND-2026 en BORRADOR (D-50), sus SO y PI, el plan de estudios con el ciclo",
        "-- de malla y los pares asignatura y SO, con el «Portafolio 3» de 5643 y SO 6. No trae rúbricas, competencias ni",
        f"-- estadíos. {len(ya.keys() & asig.keys())} asignaturas ya están en V1_03 y se reutilizan con su nombre, "
        f"y las {len(nuevas)} nuevas se insertan aquí.",
        "",
        "INSERT INTO abet.carrera (facultad_id, codigo, nombre)",
        f"SELECT facultad_id, {q(CARRERA)}, {q(d['carrera'])} FROM abet.facultad WHERE codigo = {q(FACULTAD)};",
        "",
        "INSERT INTO abet.catalogo_version (carrera_id, codigo, estado, huella_fuente)",
        f"SELECT carrera_id, {q(CATALOGO)}, 'BORRADOR', {q(huella)} FROM abet.carrera WHERE codigo = {q(CARRERA)};",
        "",
        "INSERT INTO abet.asignatura (codigo, nombre) VALUES",
        valores(sorted(nuevas.items())) + ";",
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
        "INSERT INTO abet.instrumento (catalogo_version_id, nombre)",
        "SELECT cv.catalogo_version_id, v.nombre FROM (VALUES",
        valores([(i,) for i in inst]),
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
        "-- Aserción de carga. La migración falla, y Flyway la deshace, si algún conteo de IND-2026 no coincide con el",
        "-- JSON. Cuenta solo las filas de IND-2026, así AMB-2026 y las asignaturas de otras carreras no la mueven.",
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
        ("plan_estudios", "SELECT count(*) FROM abet.plan_estudios WHERE catalogo_version_id = v_version"),
        ("asignatura_so", "SELECT count(*) FROM abet.asignatura_so WHERE catalogo_version_id = v_version"),
        ("asignatura_competencia", "SELECT count(*) FROM abet.asignatura_competencia WHERE catalogo_version_id = v_version"),
        ("instrumento", "SELECT count(*) FROM abet.instrumento WHERE catalogo_version_id = v_version"),
    ]
    for tabla, sql in chequeos:
        L += [f"    {sql} INTO v_n;",
              f"    IF v_n <> {conteos[tabla]} THEN",
              f"        RAISE EXCEPTION 'abet.{tabla} de {CATALOGO}: se esperaban {conteos[tabla]} filas y hay %', v_n;",
              "    END IF;"]
    L += ["END;", "$$;", ""]
    with open(ruta_sql, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        falla("uso, generar_v1_12.py <referencia.json> <salida.sql>")
    main(sys.argv[1], sys.argv[2])
