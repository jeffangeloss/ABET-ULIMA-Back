"""Pasos de catalogo_industrial.feature (US-67 a US-69 de la spec 008), con pytest-bdd en español (T020 a T022 y T025).

El .feature manda. Cada «Entonces» se comprueba contra la base desechable del escenario, la salida del generador o la
de psql, sin dobles del sistema bajo prueba. «Flyway aplica» corre la migración con psql -1, como
tests/base_desechable.py y db/pruebas/correr_pruebas.sh, cada una en su transacción. Las bases viven en el clúster
desechable de tests/cluster_desechable.py y nunca en localhost:5432.

Cada escenario se ata con @scenario y el nombre de su tarea, porque el .feature mezcla escenarios de la base (T020 a
T022 y T025) con los de la comprobación de arranque de la API (T033), que llegan con su propia tarea. La referencia
inventada de los esquemas se arma en tmp_path desde db/referencia/industrial_2026.json, que trae solo datos
curriculares, y el archivo de salida del generador también cae en tmp_path.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
from pytest_bdd import given, parsers, scenario, then, when

from abet_carga.carga import Configuracion, ConfiguracionInvalida, cargar
from app.configuracion import ConfiguracionDeLaApi

Escenario = Any
A = sys.modules["api_de_prueba"]
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/catalogo_industrial.feature"
REFERENCIA = RAIZ / "db" / "referencia" / "industrial_2026.json"
GENERADOR = RAIZ / "db" / "herramientas" / "generar_v1_12.py"
MIGRACIONES = RAIZ / "db" / "migration"
V1_12 = MIGRACIONES / "V1_12__cargar_referencia_industrial.sql"
V1_13 = MIGRACIONES / "V1_13__cargar_reglas_industrial.sql"
V1_14 = MIGRACIONES / "V1_14__crear_coordinacion_alcance.sql"
CORRER_PRUEBAS = RAIZ / "db" / "pruebas" / "correr_pruebas.sh"
# Tablas del catálogo de AMB-2026 que V1_12 no debe tocar, con la columna que las ata a la versión.
TABLAS_DE_AMB = {
    "so": "SELECT so_id, numero, descripcion FROM abet.so WHERE catalogo_version_id = %s ORDER BY 1",
    "pi": "SELECT pi_id, codigo, descripcion FROM abet.pi WHERE catalogo_version_id = %s ORDER BY 1",
    "rubrica_nivel": "SELECT r.pi_id, r.nivel, r.descriptor FROM abet.rubrica_nivel r JOIN abet.pi p USING (pi_id)"
                     " WHERE p.catalogo_version_id = %s ORDER BY 1, 2",
    "plan_estudios": "SELECT asignatura_id, ciclo_malla FROM abet.plan_estudios WHERE catalogo_version_id = %s"
                     " ORDER BY 1",
    "asignatura_so": "SELECT asignatura_id, so_id, instrumento_id FROM abet.asignatura_so"
                     " WHERE catalogo_version_id = %s ORDER BY 1, 2",
}


# Ayudas

def _bd(ctx: Escenario) -> Any:
    return ctx.plantillas.base_desechable


def psql(ctx: Escenario, *argumentos: str, entorno: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """psql sobre la base del escenario, en el clúster desechable, sin lanzar para que el paso lea el código."""
    variables = {**_bd(ctx)._entorno(), **(entorno or {})}
    return subprocess.run([variables.get("PSQL", "psql"), "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d",
                           ctx.api.base.nombre, *argumentos], env=variables, capture_output=True, text=True,
                          check=False)


def aplicar(ctx: Escenario, migracion: Path) -> None:
    """Aplica una migración como Flyway, en una sola transacción, y exige que termine bien."""
    corrida = psql(ctx, "-1", "-f", str(migracion), entorno={"PGOPTIONS": "-c client_min_messages=warning"})
    assert corrida.returncode == 0, f"{migracion.name}: {corrida.stderr.strip()}"
    if migracion.name.startswith("V1_14__"):
        # En Neon, crear_rol_app.sql corre otra vez después de V1_14 y da al rol de la aplicación el SELECT de la tabla
        # de alcance, que app/permisos.py lee desde T030. Aquí el rol ya existe, así que el dueño da ese mismo SELECT.
        ctx.api.dueno.execute(f'GRANT SELECT ON acceso.coordinacion_alcance TO "{ctx.api.base.rol_app}"')


def generar(entrada: Path, salida: Path) -> subprocess.CompletedProcess[str]:
    """Corre generar_v1_12.py con python -I, como db/pruebas/correr_pruebas.sh corre generar_v1_03.py."""
    assert GENERADOR.exists(), "falta db/herramientas/generar_v1_12.py (T020)"
    return subprocess.run([sys.executable, "-I", str(GENERADOR), str(entrada), str(salida)], capture_output=True,
                          text=True, check=False)


def version(ctx: Escenario, codigo: str) -> int | None:
    filas = ctx.filas("SELECT catalogo_version_id FROM abet.catalogo_version WHERE codigo = %s", codigo)
    return filas[0][0] if filas else None


def foto_de_amb(ctx: Escenario) -> dict[str, list[tuple[Any, ...]]]:
    amb = version(ctx, "AMB-2026")
    return {tabla: ctx.filas(consulta, amb) for tabla, consulta in TABLAS_DE_AMB.items()}


def _corre_control(ctx: Escenario, control: str) -> None:
    """Consulta de control de controles_neon.sql sobre la base del escenario, con las ayudas de conftest.py."""
    for plugin in ctx.request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            ctx.extras["control"] = ctx.filas(plugin.consultas_de_control()[control])
            return
    raise AssertionError("no se encuentra tests/aceptacion/pasos/conftest.py")


def _tmp(ctx: Escenario) -> Path:
    return ctx.request.getfixturevalue("tmp_path")


# US-67. Escenarios de T020

@scenario(FEATURE, "La migración V1_12 carga el catálogo IND-2026 con sus conteos")
def test_v1_12_carga_ind_2026_con_sus_conteos() -> None:
    """T020."""


@scenario(FEATURE, "Una asignatura compartida se reutiliza sin tocar Ambiental")
def test_una_asignatura_compartida_se_reutiliza_sin_tocar_ambiental() -> None:
    """T020."""


@scenario(FEATURE, "La sección 1 de pruebas.sql cuenta por catálogo y no en toda la base")
def test_la_seccion_1_de_pruebas_sql_cuenta_por_catalogo() -> None:
    """T020."""


@scenario(FEATURE, "El generador de V1_12 es determinista")
def test_el_generador_de_v1_12_es_determinista() -> None:
    """T020."""


@scenario(FEATURE, "El generador rechaza una referencia mal formada antes de escribir")
def test_el_generador_rechaza_una_referencia_mal_formada() -> None:
    """T020."""


@scenario(FEATURE, "La aserción final detiene la migración si un conteo no coincide")
def test_la_asercion_final_detiene_la_migracion() -> None:
    """T020."""


# Dado

@given(parsers.re(r'que abet\.asignatura ya tiene "(?P<codigo>[0-9]+)" con el nombre "(?P<nombre>[^"]+)" desde V1_03'))
def _asignatura_registrada(ctx: Escenario, codigo: str, nombre: str) -> None:
    assert ctx.filas("SELECT nombre FROM abet.asignatura WHERE codigo = %s", codigo) == [(nombre,)]
    assert f"('{codigo}', '{nombre}')" in (MIGRACIONES / "V1_03__cargar_referencia_ambiental.sql").read_text("utf-8")


@given(parsers.re(r'la base con V1_12 aplicada$'))
def _con_v1_12(ctx: Escenario) -> None:
    aplicar(ctx, V1_12)


@given(parsers.re(r'una referencia inventada con (?P<defecto>.+)'))
def _referencia_inventada(ctx: Escenario, defecto: str) -> None:
    datos = json.loads(REFERENCIA.read_text(encoding="utf-8"))
    pis, pares = datos["pi"], datos["asignatura_pi"]
    if defecto == 'un PI "8.1" de un SO 8 que no existe':
        pis[-1] = {**pis[-1], "codigo": "8.1", "so": 8}
    elif defecto == 'dos PI con el código "2.3"':
        indice = next(i for i, p in enumerate(pis) if p["codigo"] == "2.2")
        pis[indice] = {**pis[indice], "codigo": "2.3"}
    elif defecto == 'la asignatura "56430" de 5 dígitos':
        indice = next(i for i, x in enumerate(pares) if x["codigo"] == "5643")
        pares[indice] = {**pares[indice], "codigo": "56430"}
    elif defecto == 'la asignatura "5643" con el nombre "Quimica general"':
        indice = next(i for i, x in enumerate(pares) if x["codigo"] == "5643")
        pares[indice] = {**pares[indice], "asignatura": "Quimica general"}
    elif defecto == "una descripción de PI de 301 caracteres":
        pis[0] = {**pis[0], "descripcion": "Texto inventado " + "x" * 285}
        assert len(pis[0]["descripcion"]) == 301
    elif defecto == "una asignatura de nivel 13":
        pares[0] = {**pares[0], "nivel": 13}
    elif defecto == "una asignatura sin nivel":
        pares[0] = {clave: valor for clave, valor in pares[0].items() if clave != "nivel"}
    else:
        raise AssertionError(f"defecto sin regla: {defecto}")
    ruta = _tmp(ctx) / "referencia_inventada.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    ctx.extras["referencia"] = ruta


@given(parsers.re(r'una copia de V1_12 sin una de sus 21 filas de PI'))
def _copia_sin_un_pi(ctx: Escenario) -> None:
    lineas = V1_12.read_text(encoding="utf-8").split("\n")
    # La fila del PI 3.2, en medio de la lista, así la sentencia sigue bien formada sin ella.
    filas = [i for i, linea in enumerate(lineas) if re.match(r" \(3, 2, '3\.2', ", linea)]
    assert len(filas) == 1, "V1_12 no trae una sola fila del PI 3.2"
    del lineas[filas[0]]
    ruta = _tmp(ctx) / "V1_12_sin_un_pi.sql"
    ruta.write_text("\n".join(lineas), encoding="utf-8")
    ctx.extras["copia"] = ruta


# Cuando

@when(parsers.re(r'Flyway aplica V1_12__cargar_referencia_industrial\.sql'))
def _flyway_aplica_v1_12(ctx: Escenario) -> None:
    ctx.extras["amb_antes"] = foto_de_amb(ctx)
    ctx.extras["asignaturas_antes"] = ctx.uno("SELECT count(*) FROM abet.asignatura")
    aplicar(ctx, V1_12)


@when(parsers.re(r'corre db/pruebas/correr_pruebas\.sh'))
def _corre_correr_pruebas(ctx: Escenario) -> None:
    ctx.extras["corrida"] = subprocess.run(["bash", str(CORRER_PRUEBAS)], cwd=RAIZ, capture_output=True, text=True,
                                           check=False)


@when(parsers.re(r'db/herramientas/generar_v1_12\.py corre dos veces con la misma referencia'))
def _genera_dos_veces(ctx: Escenario) -> None:
    salidas = [_tmp(ctx) / "primera.sql", _tmp(ctx) / "segunda.sql"]
    for salida in salidas:
        corrida = generar(REFERENCIA, salida)
        assert corrida.returncode == 0, corrida.stderr
    ctx.extras["salidas"] = salidas


@when(parsers.re(r'corre db/herramientas/generar_v1_12\.py$'))
def _genera_con_la_inventada(ctx: Escenario) -> None:
    salida = _tmp(ctx) / "salida.sql"
    ctx.extras["salida"] = salida
    ctx.extras["generacion"] = generar(ctx.extras["referencia"], salida)


@when(parsers.re(r'Flyway la aplica en una transacción en una base desechable'))
def _flyway_aplica_la_copia(ctx: Escenario) -> None:
    ctx.extras["aplicacion"] = psql(ctx, "-1", "-f", str(ctx.extras["copia"]),
                                    entorno={"PGOPTIONS": "-c client_min_messages=warning"})


# Entonces

@then(parsers.re(r'abet\.carrera tiene la carrera "(?P<codigo>[A-Z]+)" con el nombre "(?P<nombre>[^"]+)" en la '
                 r'facultad "(?P<facultad>[A-Z]+)"'))
def _carrera(ctx: Escenario, codigo: str, nombre: str, facultad: str) -> None:
    assert ctx.filas("SELECT c.nombre, f.codigo FROM abet.carrera c JOIN abet.facultad f USING (facultad_id)"
                     " WHERE c.codigo = %s", codigo) == [(nombre, facultad)]


@then(parsers.re(r'abet\.catalogo_version tiene "(?P<codigo>[A-Z]+-[0-9]+)" en estado "(?P<estado>[A-Z]+)" con la '
                 r'huella SHA-256 de la referencia'))
def _catalogo(ctx: Escenario, codigo: str, estado: str) -> None:
    huella = hashlib.sha256(REFERENCIA.read_bytes()).hexdigest()
    assert ctx.filas("SELECT cv.estado, cv.huella_fuente, c.codigo FROM abet.catalogo_version cv"
                     " JOIN abet.carrera c USING (carrera_id) WHERE cv.codigo = %s", codigo) == [(estado, huella, "IND")]


@then(parsers.re(r'IND-2026 tiene (?P<so>[0-9]+) filas en abet\.so, (?P<pi>[0-9]+) en abet\.pi, (?P<plan>[0-9]+) en '
                 r'abet\.plan_estudios y (?P<rubrica>[0-9]+) en abet\.rubrica_nivel'))
def _conteos_ind(ctx: Escenario, so: str, pi: str, plan: str, rubrica: str) -> None:
    ind = version(ctx, "IND-2026")
    assert ctx.cuenta("so", "catalogo_version_id = %s", ind) == int(so)
    assert ctx.cuenta("pi", "catalogo_version_id = %s", ind) == int(pi)
    assert ctx.cuenta("plan_estudios", "catalogo_version_id = %s", ind) == int(plan)
    assert ctx.uno("SELECT count(*) FROM abet.rubrica_nivel r JOIN abet.pi p USING (pi_id)"
                   " WHERE p.catalogo_version_id = %s", ind) == int(rubrica)


@then(parsers.re(r'el PI "(?P<pi>[0-9.]+)" de IND-2026 pertenece al SO (?P<so>[0-9]+) y el par (?P<asignatura>[0-9]+) y '
                 r'SO (?P<so_par>[0-9]+) está en abet\.asignatura_so'))
def _pi_y_par(ctx: Escenario, pi: str, so: str, asignatura: str, so_par: str) -> None:
    ind = version(ctx, "IND-2026")
    assert ctx.filas("SELECT s.numero FROM abet.pi p JOIN abet.so s USING (so_id)"
                     " WHERE p.catalogo_version_id = %s AND p.codigo = %s", ind, pi) == [(int(so),)]
    assert ctx.uno("SELECT count(*) FROM abet.asignatura_so x JOIN abet.asignatura a USING (asignatura_id)"
                   " JOIN abet.so s ON s.so_id = x.so_id WHERE x.catalogo_version_id = %s AND a.codigo = %s"
                   " AND s.numero = %s", ind, asignatura, int(so_par)) == 1


@then(parsers.re(r'abet\.instrumento tiene «(?P<nombre>[^»]+)» en IND-2026'))
def _instrumento(ctx: Escenario, nombre: str) -> None:
    ind = version(ctx, "IND-2026")
    assert ctx.uno("SELECT count(*) FROM abet.instrumento WHERE catalogo_version_id = %s AND nombre = %s",
                   ind, nombre) == 1
    # El instrumento es el del par 5643 y SO 6, que el plan de medición copia.
    assert ctx.filas("SELECT i.nombre FROM abet.asignatura_so x JOIN abet.asignatura a USING (asignatura_id)"
                     " JOIN abet.so s ON s.so_id = x.so_id JOIN abet.instrumento i ON i.instrumento_id = x.instrumento_id"
                     " WHERE x.catalogo_version_id = %s AND a.codigo = '5643' AND s.numero = 6", ind) == [(nombre,)]


@then(parsers.re(r'abet\.asignatura sigue con una sola fila de código "(?P<codigo>[0-9]+)" y el mismo nombre'))
def _una_sola_fila(ctx: Escenario, codigo: str) -> None:
    assert ctx.filas("SELECT nombre FROM abet.asignatura WHERE codigo = %s", codigo) == [("Química General",)]


@then(parsers.re(r'abet\.asignatura gana (?P<nuevas>[0-9]+) filas y queda con (?P<total>[0-9]+)'))
def _asignaturas_nuevas(ctx: Escenario, nuevas: str, total: str) -> None:
    ahora = ctx.uno("SELECT count(*) FROM abet.asignatura")
    assert ahora - ctx.extras["asignaturas_antes"] == int(nuevas)
    assert ahora == int(total)


@then(parsers.re(r'"(?P<codigo>[0-9]+)" está en el plan de estudios de AMB-2026 y en el de IND-2026'))
def _en_los_dos_planes(ctx: Escenario, codigo: str) -> None:
    assert [fila[0] for fila in ctx.filas(
        "SELECT cv.codigo FROM abet.plan_estudios pe JOIN abet.catalogo_version cv USING (catalogo_version_id)"
        " JOIN abet.asignatura a USING (asignatura_id) WHERE a.codigo = %s ORDER BY 1", codigo)] == ["AMB-2026",
                                                                                                    "IND-2026"]


@then(parsers.re(r'las filas de AMB-2026 en abet\.so, abet\.pi, abet\.rubrica_nivel, abet\.plan_estudios y '
                 r'abet\.asignatura_so no cambian'))
def _amb_sin_cambios(ctx: Escenario) -> None:
    antes = ctx.extras["amb_antes"]
    assert all(antes[tabla] for tabla in antes if tabla != "rubrica_nivel")
    assert foto_de_amb(ctx) == antes


@then(parsers.re(r'las aserciones de AMB-2026 cuentan solo las filas del catálogo AMB-2026'))
def _asercion_de_amb(ctx: Escenario) -> None:
    corrida = ctx.extras["corrida"]
    assert corrida.returncode == 0, corrida.stdout[-3000:] + corrida.stderr[-2000:]
    assert "ok C01 catálogo AMB-2026 con los conteos de la referencia, contados solo en AMB-2026" in corrida.stdout
    texto = (RAIZ / "db" / "pruebas" / "pruebas.sql").read_text(encoding="utf-8")
    seccion = texto.split("-- 2. Casos que deben aceptarse")[0]
    # Ninguna cuenta de la sección 1 sobre una tabla del catálogo queda sin el filtro por versión.
    for tabla in ("so", "pi", "plan_estudios", "asignatura_so", "competencia", "competencia_so",
                  "asignatura_competencia", "instrumento"):
        # Cada cuenta llega hasta la siguiente del UNION ALL o hasta el LOOP, aunque ocupe varias líneas.
        for cuenta in re.findall(rf"count\(\*\) FROM abet\.{tabla}\b.*?(?=UNION ALL|\n\s*LOOP)", seccion, flags=re.S):
            assert "catalogo_version_id" in cuenta, f"pruebas.sql cuenta abet.{tabla} sin el catálogo: {cuenta}"


@then(parsers.re(r'una aserción nueva cuenta las filas de IND-2026'))
def _asercion_de_ind(ctx: Escenario) -> None:
    assert "ok C02 catálogo IND-2026 con los conteos de la referencia" in ctx.extras["corrida"].stdout


@then(parsers.re(r'la corrida termina sin ninguna línea «FALLA»'))
def _sin_falla(ctx: Escenario) -> None:
    corrida = ctx.extras["corrida"]
    assert "FALLA" not in corrida.stdout + corrida.stderr
    assert corrida.stdout.rstrip().splitlines()[-1] == "RESULTADO: todo pasó"


@then(parsers.re(r'los dos archivos salen iguales byte a byte'))
def _iguales(ctx: Escenario) -> None:
    primera, segunda = ctx.extras["salidas"]
    assert primera.read_bytes() == segunda.read_bytes()


@then(parsers.re(r'la prueba regenera V1_12 y no encuentra diferencias con el archivo guardado'))
def _igual_a_la_guardada(ctx: Escenario) -> None:
    assert ctx.extras["salidas"][0].read_bytes() == V1_12.read_bytes()


@then(parsers.re(r'termina con código (?P<codigo>[0-9])$'))
def _codigo(ctx: Escenario, codigo: str) -> None:
    assert ctx.extras["generacion"].returncode == int(codigo), ctx.extras["generacion"].stderr


@then(parsers.re(r'el mensaje nombra (?P<motivo>.+)'))
def _motivo(ctx: Escenario, motivo: str) -> None:
    assert motivo in ctx.extras["generacion"].stderr, ctx.extras["generacion"].stderr


@then(parsers.re(r'no escribe el archivo de salida'))
def _sin_salida(ctx: Escenario) -> None:
    assert not ctx.extras["salida"].exists()


@then(parsers.re(r'la migración falla con el conteo de abet\.pi'))
def _falla_por_el_conteo(ctx: Escenario) -> None:
    aplicacion = ctx.extras["aplicacion"]
    assert aplicacion.returncode == 3, aplicacion.stderr
    assert "abet.pi de IND-2026: se esperaban 21 filas y hay 20" in aplicacion.stderr, aplicacion.stderr


@then(parsers.re(r'ninguna fila de IND-2026 queda en la base'))
def _sin_ind(ctx: Escenario) -> None:
    assert ctx.uno("SELECT count(*) FROM abet.carrera WHERE codigo = 'IND'") == 0
    assert version(ctx, "IND-2026") is None
    assert ctx.uno("SELECT count(*) FROM abet.asignatura") == 53



# US-68. Escenarios de T021 (los de la carga de 5643 llegan con T024, porque usan los datos inventados de Química)

@scenario(FEATURE, "La migración V1_13 siembra el conjunto de reglas de Industrial")
def test_v1_13_siembra_el_conjunto_de_industrial() -> None:
    """T021."""


@scenario(FEATURE, "Una carga de 450002 sigue con las reglas de Ambiental")
def test_una_carga_de_450002_sigue_con_las_reglas_de_ambiental() -> None:
    """T021."""


PARAMETROS = ("META_LOGRO", "NIVEL_ESPERADO", "CORTE_ROJO", "CONVERSION_NIVEL_0_1", "TRATO_SIN_EVIDENCIA")
EXPORT_410 = "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-36-02.xlsx"


def parametros_de(ctx: Escenario, carrera: str) -> dict[str, tuple[str, Any]]:
    return {clave: (estado, valor) for clave, estado, valor in ctx.filas(
        "SELECT pv.clave, pv.estado, pv.valor_numero FROM abet.parametro_valor pv"
        " JOIN abet.conjunto_reglas cr USING (conjunto_reglas_id) JOIN abet.carrera c USING (carrera_id)"
        " WHERE c.codigo = %s AND cr.version = 'R-2026-BORRADOR'", carrera)}


@given(parsers.re(r'la base con V1_12 y V1_13 aplicadas y la sección inventada (?P<numero>[0-9]+) de '
                  r'(?P<asignatura>[0-9]+) en (?P<periodo>[0-9]{4}-[0-9])$'))
def _con_v1_13_y_la_410(ctx: Escenario, numero: str, asignatura: str, periodo: str) -> None:
    aplicar(ctx, V1_12)
    aplicar(ctx, V1_13)
    # Desde T030 la API lee acceso.coordinacion_alcance, así que corre después de V1_14, como en el orden de FR-020.
    aplicar(ctx, V1_14)
    assert ctx.uno("SELECT count(*) FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                   " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id WHERE s.numero = %s AND a.codigo = %s"
                   " AND pe.codigo = %s", numero, asignatura, periodo) == 1


@when(parsers.re(r'Flyway aplica V1_13__cargar_reglas_industrial\.sql'))
def _flyway_aplica_v1_13(ctx: Escenario) -> None:
    ctx.extras["amb_reglas_antes"] = parametros_de(ctx, "AMB")
    aplicar(ctx, V1_13)


@when(parsers.re(r'"(?P<correo>[^"]+)" sube a la (?P<numero>[0-9]+) un export inventado válido'))
def _sube_valido(ctx: Escenario, correo: str, numero: str) -> None:
    ctx.subir(correo, ctx.de_inventados(EXPORT_410), EXPORT_410, seccion=numero)


@then(parsers.re(r'abet\.conjunto_reglas tiene "(?P<version>[^"]+)" en "(?P<estado>[A-Z]+)" para "(?P<una>[A-Z]+)" y '
                 r'otro para "(?P<otra>[A-Z]+)"'))
def _conjuntos(ctx: Escenario, version: str, estado: str, una: str, otra: str) -> None:
    assert ctx.filas("SELECT c.codigo, cr.estado, cr.aprobado_por, cr.aprobado_en FROM abet.conjunto_reglas cr"
                     " JOIN abet.carrera c USING (carrera_id) WHERE cr.version = %s ORDER BY c.codigo", version) == [
        (otra, estado, None, None), (una, estado, None, None)]


@then(parsers.re(r'el de "(?P<carrera>[A-Z]+)" define META_LOGRO en 0,80 y NIVEL_ESPERADO en 3'))
def _definidos(ctx: Escenario, carrera: str) -> None:
    parametros = parametros_de(ctx, carrera)
    assert parametros["META_LOGRO"] == ("DEFINIDO", Decimal("0.8000"))
    assert parametros["NIVEL_ESPERADO"] == ("DEFINIDO", Decimal("3.0000"))


@then(parsers.re(r'deja CORTE_ROJO, CONVERSION_NIVEL_0_1 y TRATO_SIN_EVIDENCIA en PENDIENTE, como el de "(?P<otra>[A-Z]+)"'))
def _pendientes(ctx: Escenario, otra: str) -> None:
    ind, amb = parametros_de(ctx, "IND"), parametros_de(ctx, otra)
    assert set(ind) == set(PARAMETROS)
    for clave in ("CORTE_ROJO", "CONVERSION_NIVEL_0_1", "TRATO_SIN_EVIDENCIA"):
        assert ind[clave] == ("PENDIENTE", None)
    # Los mismos parámetros que Ambiental, y el conjunto de Ambiental no cambia.
    assert ind == amb == ctx.extras["amb_reglas_antes"]


@then(parsers.re(r'la carga queda PUBLICADA con la carrera "(?P<carrera>[A-Z]+)" y el conjunto R-2026-BORRADOR de '
                 r'"(?P<reglas>[A-Z]+)"'))
def _publicada_con_sus_reglas(ctx: Escenario, carrera: str, reglas: str) -> None:
    assert ctx.respuesta.status_code == 201, ctx.respuesta.text
    assert ctx.carga_id is not None
    assert ctx.filas("SELECT c.estado, ca.codigo, cr.version, cc.codigo FROM abet.carga c"
                     " JOIN abet.carrera ca ON ca.carrera_id = c.carrera_id"
                     " JOIN abet.conjunto_reglas cr ON cr.conjunto_reglas_id = c.conjunto_reglas_id"
                     " JOIN abet.carrera cc ON cc.carrera_id = cr.carrera_id WHERE c.carga_id = %s",
                     ctx.carga_id) == [("PUBLICADA", carrera, "R-2026-BORRADOR", reglas)]


# US-68. Escenarios de T024 y Q19 de T021, que usan el guion del plan y los datos inventados de Química

@scenario(FEATURE, "Una carga de 5643 toma las reglas de Industrial y la vista da la regla de la meta")
def test_una_carga_de_5643_toma_las_reglas_de_industrial() -> None:
    """T024."""


@scenario(FEATURE, "Sin el conjunto de Industrial la biblioteca no guarda nada y la ruta responde el error interno")
def test_sin_el_conjunto_de_industrial_la_biblioteca_no_guarda_nada() -> None:
    """T024."""


@scenario(FEATURE, "Q19 lista una carrera con plan de medición sin conjunto de reglas")
def test_q19_lista_una_carrera_con_plan_sin_conjunto_de_reglas() -> None:
    """T021."""


@scenario(FEATURE, "El arranque de la API revisa el conjunto de reglas de cada carrera con plan")
def test_el_arranque_revisa_el_conjunto_de_cada_carrera() -> None:
    """T033."""


# US-69. Escenarios de T022 y T025

@scenario(FEATURE, "La corrida en seco del plan de Química informa y no escribe")
def test_la_corrida_en_seco_del_plan_informa_y_no_escribe() -> None:
    """T022."""


@scenario(FEATURE, "Con aplicar quedan la vigencia y el plan de 5643 con el PI 6.1")
def test_con_aplicar_quedan_la_vigencia_y_el_plan() -> None:
    """T022."""


@scenario(FEATURE, "Repetir el guion del plan no duplica ni cambia filas")
def test_repetir_el_guion_del_plan_no_duplica() -> None:
    """T022."""


@scenario(FEATURE, "Una fila de plan distinta detiene todo")
def test_una_fila_de_plan_distinta_detiene_todo() -> None:
    """T022."""


@scenario(FEATURE, "Una descripción del instrumento inválida no entra")
def test_una_descripcion_del_instrumento_invalida_no_entra() -> None:
    """T022."""


@scenario(FEATURE, "Sin el par 5643 y SO 6 en el catálogo el plan no entra")
def test_sin_el_par_5643_y_so_6_el_plan_no_entra() -> None:
    """T022."""


@scenario(FEATURE, "Ambiental en 2026-2 queda igual tras el plan de Química")
def test_ambiental_en_2026_2_queda_igual_tras_el_plan() -> None:
    """T022 y T025."""


@scenario(FEATURE, "Q18 detecta un curso con plan de dos carreras en el mismo periodo")
def test_q18_detecta_un_curso_con_plan_de_dos_carreras() -> None:
    """T022."""


PLAN = RAIZ / "db" / "datos" / "plan_quimica_2026_1.sql"
ALCANCE_AMB = RAIZ / "db" / "datos" / "alcance_coordinacion_ambiental.sql"
QUIMICA = RAIZ / "db" / "datos" / "quimica_2026_1_inventado.sql"
HUELLA = RAIZ / "db" / "plataforma" / "neon" / "huella_ambiental.sql"
DESCRIPCION = "Texto de prueba del Portafolio 3"
NOMBRE_701 = "gc_SINTETICO_20261_5643_701_fullgc_2026-07-15-00-00-00.xlsx"
TABLAS_DEL_PLAN = ("catalogo_vigencia", "plan_medicion")


def _aplicadas(ctx: Escenario, *migraciones: Path) -> None:
    """Aplica cada migración una sola vez por escenario, en el orden dado."""
    hechas = ctx.extras.setdefault("aplicadas", set())
    for migracion in migraciones:
        if migracion not in hechas:
            aplicar(ctx, migracion)
            hechas.add(migracion)


def correr_plan(ctx: Escenario, *variables: str, descripcion: str | None = DESCRIPCION) -> subprocess.CompletedProcess[str]:
    """Guion del plan con psql, con la descripción por la variable de entorno y VERBOSITY=verbose para leer el SQLSTATE."""
    entorno = {"DESCRIPCION_INSTRUMENTO": descripcion} if descripcion is not None else {}
    argumentos = [parte for variable in variables for parte in ("-v", variable)]
    corrida = psql(ctx, "-v", "VERBOSITY=verbose", *argumentos, "-f", str(PLAN), entorno=entorno)
    ctx.extras["corrida_plan"] = corrida
    return corrida


def correr_datos(ctx: Escenario, guion: Path, *variables: str) -> None:
    argumentos = [parte for variable in variables for parte in ("-v", variable)]
    corrida = psql(ctx, *argumentos, "-f", str(guion))
    assert corrida.returncode == 0, f"{guion.name}: {corrida.stderr.strip()}"


def filas_del_plan(ctx: Escenario) -> list[tuple[Any, ...]]:
    return ctx.filas(
        "SELECT pe.codigo, c.codigo, cv.codigo, a.codigo, p.codigo, s.numero, i.nombre, pm.descripcion_instrumento"
        " FROM abet.plan_medicion pm JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id"
        " JOIN abet.carrera c ON c.carrera_id = pm.carrera_id"
        " JOIN abet.catalogo_version cv ON cv.catalogo_version_id = pm.catalogo_version_id"
        " JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id JOIN abet.pi p ON p.pi_id = pm.pi_id"
        " JOIN abet.so s ON s.so_id = pm.so_id LEFT JOIN abet.instrumento i ON i.instrumento_id = pm.instrumento_id"
        " ORDER BY 1, 4, 5")


def filas_de_vigencia(ctx: Escenario) -> list[tuple[Any, ...]]:
    return ctx.filas("SELECT pe.codigo, c.codigo, cv.codigo FROM abet.catalogo_vigencia v"
                     " JOIN abet.periodo pe USING (periodo_id) JOIN abet.carrera c USING (carrera_id)"
                     " JOIN abet.catalogo_version cv ON cv.catalogo_version_id = v.catalogo_version_id ORDER BY 1, 2")


def huella_ambiental(ctx: Escenario) -> str:
    corrida = psql(ctx, "-f", str(HUELLA))
    assert corrida.returncode == 0, corrida.stderr
    assert "@" not in corrida.stdout and not re.search(r"\b[0-9]{8}\b", corrida.stdout)
    assert re.search(r"HUELLA DE AMBIENTAL \| +[0-9]+ \| [0-9a-f]{64}", corrida.stdout), corrida.stdout
    return corrida.stdout


def seccion_de_5643(ctx: Escenario, numero: str) -> int:
    return int(ctx.uno("SELECT s.seccion_id FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                       " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
                       " WHERE a.codigo = '5643' AND pe.codigo = '2026-1' AND s.numero = %s", numero))


def export_701(ctx: Escenario, niveles: list[int]) -> bytes:
    """Export inventado de la 701 en memoria, con la hoja que declara la sección y la columna del PI 6.1."""
    g = ctx.generador
    filas = tuple((f"Inventado {n:02d}", "Estudiante", 99100000 + n, nivel) for n, nivel in enumerate(niveles, start=1))
    return bytes(g.a_bytes(g.Export("gc_SINTETICO_20261_5643_701_f",
                                    ("Last Name", "First Name", "Username", "ABET SO6.1 [Total Pts: 4 Score] |9000061"),
                                    filas)))


def _quimica(ctx: Escenario, *migraciones: Path) -> None:
    """Migraciones dadas, el alcance de Ambiental, el plan de 5643 en 2026-1 y los datos inventados de Química."""
    _aplicadas(ctx, *migraciones)
    correr_datos(ctx, ALCANCE_AMB, "aplicar=1")
    assert correr_plan(ctx, "aplicar=1", "pi=6.1").returncode == 0, ctx.extras["corrida_plan"].stderr
    correr_datos(ctx, QUIMICA)


# Dado

@given(parsers.re(r'la base con V1_12 a V1_14 aplicadas, el plan de 5643 en 2026-1 y los datos de '
                  r'db/datos/quimica_2026_1_inventado\.sql'))
def _quimica_con_reglas(ctx: Escenario) -> None:
    _quimica(ctx, V1_12, V1_13, V1_14)


@given(parsers.re(r'la base con V1_12 y V1_14 sin V1_13, el plan de 5643 en 2026-1 y los datos de '
                  r'db/datos/quimica_2026_1_inventado\.sql'))
def _quimica_sin_reglas(ctx: Escenario) -> None:
    # Desde T033 la API no arranca sin el conjunto de cada carrera con plan, así que la sesión del profesor de la 701
    # se abre con V1_13 aplicada y después se quita el conjunto de IND, el único efecto de V1_13. El escenario prueba la
    # biblioteca y la ruta 5 con la API ya arrancada (cambio fechado del 2026-11-23 en spec.md).
    _quimica(ctx, V1_12, V1_13, V1_14)
    ctx.sesion("docente701@example.invalid")
    dueno = ctx.api.dueno
    dueno.execute("DELETE FROM abet.parametro_valor pv USING abet.conjunto_reglas cr, abet.carrera c"
                  " WHERE cr.conjunto_reglas_id = pv.conjunto_reglas_id AND c.carrera_id = cr.carrera_id"
                  " AND c.codigo = 'IND'")
    borrados = dueno.execute("DELETE FROM abet.conjunto_reglas cr USING abet.carrera c WHERE c.carrera_id = cr.carrera_id"
                             " AND c.codigo = 'IND'").rowcount
    assert borrados == 1


@given(parsers.re(r'la base con V1_12 y sin V1_13 y el plan de 5643 en 2026-1'))
def _plan_sin_reglas(ctx: Escenario) -> None:
    _aplicadas(ctx, V1_12)
    assert correr_plan(ctx, "aplicar=1").returncode == 0, ctx.extras["corrida_plan"].stderr


@given(parsers.re(r'la base con V1_12 y V1_13 aplicadas y la variable DESCRIPCION_INSTRUMENTO con "(?P<texto>[^"]+)"'))
def _con_descripcion(ctx: Escenario, texto: str) -> None:
    _aplicadas(ctx, V1_12, V1_13)
    ctx.extras["descripcion"] = texto


@given(parsers.re(r'que db/datos/plan_quimica_2026_1\.sql ya corrió con -v aplicar=1'))
def _plan_ya_corrio(ctx: Escenario) -> None:
    _aplicadas(ctx, V1_12, V1_13)
    assert correr_plan(ctx, "aplicar=1").returncode == 0, ctx.extras["corrida_plan"].stderr
    ctx.extras["foto_del_plan"] = (filas_de_vigencia(ctx), filas_del_plan(ctx))


@given(parsers.re(r'que abet\.plan_medicion ya tiene 5643 en "(?P<periodo>[^"]+)" con el PI "(?P<pi>[0-9.]+)" y el '
                  r'instrumento "(?P<instrumento>[^"]+)"'))
def _plan_distinto(ctx: Escenario, periodo: str, pi: str, instrumento: str) -> None:
    _aplicadas(ctx, V1_12, V1_13)
    dueno = ctx.api.dueno
    dueno.execute("INSERT INTO abet.instrumento (catalogo_version_id, nombre) SELECT catalogo_version_id, %s"
                  " FROM abet.catalogo_version WHERE codigo = 'IND-2026'", (instrumento,))
    dueno.execute("INSERT INTO abet.catalogo_vigencia (periodo_id, carrera_id, catalogo_version_id)"
                  " SELECT pe.periodo_id, cv.carrera_id, cv.catalogo_version_id FROM abet.periodo pe,"
                  " abet.catalogo_version cv WHERE pe.codigo = %s AND cv.codigo = 'IND-2026'", (periodo,))
    dueno.execute("INSERT INTO abet.plan_medicion (periodo_id, asignatura_id, carrera_id, catalogo_version_id, so_id,"
                  " pi_id, instrumento_id) SELECT pe.periodo_id, a.asignatura_id, cv.carrera_id, cv.catalogo_version_id,"
                  " p.so_id, p.pi_id, i.instrumento_id FROM abet.periodo pe, abet.asignatura a, abet.catalogo_version cv"
                  " JOIN abet.pi p ON p.catalogo_version_id = cv.catalogo_version_id AND p.codigo = %s"
                  " JOIN abet.instrumento i ON i.catalogo_version_id = cv.catalogo_version_id AND i.nombre = %s"
                  " WHERE pe.codigo = %s AND a.codigo = '5643' AND cv.codigo = 'IND-2026'", (pi, instrumento, periodo))


@given(parsers.re(r'la variable DESCRIPCION_INSTRUMENTO (?P<estado>ausente|con un espacio al final|con 401 caracteres)'))
def _descripcion_invalida(ctx: Escenario, estado: str) -> None:
    _aplicadas(ctx, V1_12, V1_13)
    ctx.extras["descripcion"] = {"ausente": None, "con un espacio al final": DESCRIPCION + " ",
                                 "con 401 caracteres": "Texto de prueba " + "x" * 385}[estado]
    assert estado != "con 401 caracteres" or len(ctx.extras["descripcion"]) == 401


@given(parsers.re(r'una base cuyo IND-2026 no tiene el par 5643 y SO 6 en abet\.asignatura_so'))
def _sin_el_par(ctx: Escenario) -> None:
    _aplicadas(ctx, V1_12, V1_13)
    borradas = ctx.api.dueno.execute(
        "DELETE FROM abet.asignatura_so x USING abet.catalogo_version cv, abet.asignatura a, abet.so s"
        " WHERE cv.catalogo_version_id = x.catalogo_version_id AND cv.codigo = 'IND-2026'"
        " AND a.asignatura_id = x.asignatura_id AND a.codigo = '5643' AND s.so_id = x.so_id AND s.numero = 6").rowcount
    assert borradas == 1


@given(parsers.re(r'la vigencia de AMB-2026 en 2026-2 y el plan de 450002 con los PI 5\.1, 5\.2 y 5\.3'))
def _vigencia_y_plan_de_amb(ctx: Escenario) -> None:
    _aplicadas(ctx, V1_12, V1_13)
    assert ("2026-2", "AMB", "AMB-2026") in filas_de_vigencia(ctx)
    assert [(f[3], f[4]) for f in filas_del_plan(ctx) if f[0] == "2026-2"] == [("450002", "5.1"), ("450002", "5.2"),
                                                                              ("450002", "5.3")]


@given(parsers.re(r'la huella de Ambiental tomada con db/plataforma/neon/huella_ambiental\.sql'))
def _huella_antes(ctx: Escenario) -> None:
    ctx.extras["huella"] = huella_ambiental(ctx)


@given(parsers.re(r'el plan de 5643 en "(?P<periodo>[^"]+)" con el PI "(?P<pi>[0-9.]+)" de IND-2026 y otra fila con un '
                  r'PI de AMB-2026 sembrada por error'))
def _plan_de_dos_carreras(ctx: Escenario, periodo: str, pi: str) -> None:
    _aplicadas(ctx, V1_12, V1_13)
    assert correr_plan(ctx, "aplicar=1", f"pi={pi}").returncode == 0, ctx.extras["corrida_plan"].stderr
    dueno = ctx.api.dueno
    dueno.execute("INSERT INTO abet.catalogo_vigencia (periodo_id, carrera_id, catalogo_version_id)"
                  " SELECT pe.periodo_id, cv.carrera_id, cv.catalogo_version_id FROM abet.periodo pe,"
                  " abet.catalogo_version cv WHERE pe.codigo = %s AND cv.codigo = 'AMB-2026'", (periodo,))
    dueno.execute("INSERT INTO abet.plan_medicion (periodo_id, asignatura_id, carrera_id, catalogo_version_id, so_id,"
                  " pi_id) SELECT pe.periodo_id, a.asignatura_id, cv.carrera_id, cv.catalogo_version_id, p.so_id, p.pi_id"
                  " FROM abet.periodo pe, abet.asignatura a, abet.catalogo_version cv JOIN abet.pi p"
                  " ON p.catalogo_version_id = cv.catalogo_version_id AND p.codigo = '6.1'"
                  " WHERE pe.codigo = %s AND a.codigo = '5643' AND cv.codigo = 'AMB-2026'", (periodo,))


# Cuando

@when(parsers.re(r'psql corre db/datos/plan_quimica_2026_1\.sql sin la variable aplicar'))
def _plan_en_seco(ctx: Escenario) -> None:
    ctx.antes = ctx.conteos()
    correr_plan(ctx, descripcion=ctx.extras["descripcion"])


@when(parsers.re(r'psql corre db/datos/plan_quimica_2026_1\.sql con -v aplicar=1 y -v pi=(?P<pi>[0-9.]+)'))
def _plan_aplicado(ctx: Escenario, pi: str) -> None:
    ctx.antes = ctx.conteos()
    correr_plan(ctx, "aplicar=1", f"pi={pi}", descripcion=ctx.extras["descripcion"])


@when(parsers.re(r'corre otra vez con -v aplicar=1 y la misma descripción'))
def _plan_otra_vez(ctx: Escenario) -> None:
    correr_plan(ctx, "aplicar=1")


@when(parsers.re(r'el guion del plan corre con -v aplicar=1'))
def _guion_del_plan(ctx: Escenario) -> None:
    ctx.antes = ctx.conteos()
    correr_plan(ctx, "aplicar=1", descripcion=ctx.extras.get("descripcion", DESCRIPCION))


@when(parsers.re(r'"(?P<correo>[^"]+)" sube a la 701 un export inventado con 10 estudiantes de niveles (?P<niveles>[0-9, y]+) '
                 r'en el PI "6\.1"'))
def _sube_a_la_701(ctx: Escenario, correo: str, niveles: str) -> None:
    lista = [int(n) for n in re.findall(r"[0-9]", niveles)]
    assert len(lista) == 10
    ctx.antes = ctx.conteos()
    ctx.respuesta = A.subir(ctx.sesion(correo), seccion_de_5643(ctx, "701"), export_701(ctx, lista), NOMBRE_701)
    cuerpo = ctx.cuerpo()
    ctx.carga_id = cuerpo.get("carga_id") if isinstance(cuerpo, dict) else None


@when(parsers.re(r'la biblioteca carga en la 701 un export inventado válido'))
def _biblioteca_carga(ctx: Escenario) -> None:
    ctx.antes = ctx.conteos()
    contenido = export_701(ctx, [3, 4, 2, 3])
    usuario = ctx.usuario_id("docente701@example.invalid")
    with psycopg.connect(ctx.api.base.conexion) as conexion:
        try:
            cargar(conexion, contenido, nombre_archivo=NOMBRE_701, seccion_id=seccion_de_5643(ctx, "701"),
                   usuario_id=usuario, configuracion=Configuracion(conjunto_reglas="R-2026-BORRADOR"))
        except ConfiguracionInvalida as falla:
            ctx.extras["falla"] = falla
    # La misma subida por la ruta 5, con la sesión del profesor de la 701.
    ctx.extras["ruta_5"] = A.subir(ctx.sesion("docente701@example.invalid"), seccion_de_5643(ctx, "701"), contenido,
                                   NOMBRE_701)


# Entonces

@then(parsers.re(r'abet\.v_r17_por_pi da para el PI "(?P<pi>[0-9.]+)" n_esperado_o_superior (?P<ok>[0-9]+) de '
                 r'(?P<total>[0-9]+) calificados'))
def _vista(ctx: Escenario, pi: str, ok: str, total: str) -> None:
    fila = ctx.filas("SELECT n_esperado_o_superior, n_total - n_sin_evidencia, pct_logro_sobre_calificados, meta_logro_pct, provisional"
                     " FROM abet.v_r17_por_pi WHERE carga_id = %s AND pi = %s", ctx.carga_id, pi)
    assert len(fila) == 1 and fila[0][:2] == (int(ok), int(total))
    ctx.extras["vista"] = fila[0]


@then(parsers.re(r'pct_logro_sobre_calificados es (?P<pct>[0-9]+),(?P<d1>[0-9]), meta_logro_pct es (?P<meta>[0-9]+),'
                 r'(?P<d2>[0-9]) y provisional es verdadero'))
def _porcentajes(ctx: Escenario, pct: str, d1: str, meta: str, d2: str) -> None:
    _, _, porcentaje, meta_pct, provisional = ctx.extras["vista"]
    assert porcentaje == Decimal(f"{pct}.{d1}") and meta_pct == Decimal(f"{meta}.{d2}") and provisional is True


@then(parsers.re(r'cargar\(\) lanza ConfiguracionInvalida con «(?P<mensaje>[^»]+)»'))
def _configuracion_invalida(ctx: Escenario, mensaje: str) -> None:
    assert str(ctx.extras.get("falla")) == mensaje


@then(parsers.re(r'por la ruta 5 el profesor recibe 500 con «(?P<mensaje>[^»]+)» y sin el nombre de la variable'))
def _ruta_5_error_interno(ctx: Escenario, mensaje: str) -> None:
    respuesta = ctx.extras["ruta_5"]
    assert respuesta.status_code == 500
    assert mensaje in respuesta.text
    assert "CONJUNTO_REGLAS" not in respuesta.text and "R-2026-BORRADOR" not in respuesta.text
    assert ctx.conteos()["carga"] == ctx.antes["carga"]


@then(parsers.re(r'devuelve 1 fila que nombra la carrera "(?P<carrera>[A-Z]+)" y el periodo "(?P<periodo>[^"]+)"'))
def _q19_una_fila(ctx: Escenario, carrera: str, periodo: str) -> None:
    assert ctx.extras["control"] == [(carrera, periodo)]


@then(parsers.re(r'con V1_13 aplicada devuelve 0 filas'))
def _q19_en_cero(ctx: Escenario) -> None:
    aplicar(ctx, V1_13)
    _corre_control(ctx, "Q19")
    assert ctx.extras["control"] == []


@then(parsers.re(r'el informe dice que registraría 1 vigencia y 1 fila de plan de medición'))
def _informe_en_seco(ctx: Escenario) -> None:
    corrida = ctx.extras["corrida_plan"]
    assert corrida.returncode == 0, corrida.stderr
    assert ("Plan de Química General en 2026-1 en seco. Registraría 1 vigencia y 1 fila de plan de medición. "
            "No se guardó nada, y -v aplicar=1 lo guarda.") in corrida.stdout
    assert ctx.extras["descripcion"] not in corrida.stdout + corrida.stderr


@then(parsers.re(r'abet\.catalogo_vigencia tiene IND-2026 para "(?P<carrera>[A-Z]+)" en "(?P<periodo>[^"]+)"'))
def _vigencia(ctx: Escenario, carrera: str, periodo: str) -> None:
    corrida = ctx.extras["corrida_plan"]
    assert corrida.returncode == 0, corrida.stderr
    assert "Registró 1 vigencia y 1 fila de plan de medición." in corrida.stdout
    assert (periodo, carrera, "IND-2026") in filas_de_vigencia(ctx)


@then(parsers.re(r'abet\.plan_medicion tiene para 5643 en "(?P<periodo>[^"]+)" solo el PI "(?P<pi>[0-9.]+)" del SO '
                 r'(?P<so>[0-9]+) de "(?P<carrera>[A-Z]+)"'))
def _plan_de_5643(ctx: Escenario, periodo: str, pi: str, so: str, carrera: str) -> None:
    filas = [f for f in filas_del_plan(ctx) if f[0] == periodo and f[3] == "5643"]
    assert [(f[1], f[2], f[4], f[5]) for f in filas] == [(carrera, "IND-2026", pi, int(so))]
    ctx.extras["fila_del_plan"] = filas[0]


@then(parsers.re(r'su instrumento es «(?P<instrumento>[^»]+)» y su descripción es "(?P<descripcion>[^"]+)"'))
def _instrumento_y_descripcion(ctx: Escenario, instrumento: str, descripcion: str) -> None:
    assert ctx.extras["fila_del_plan"][6:] == (instrumento, descripcion)


@then(parsers.re(r'abet\.catalogo_vigencia y abet\.plan_medicion tienen las mismas filas que antes'))
def _mismas_filas(ctx: Escenario) -> None:
    corrida = ctx.extras["corrida_plan"]
    assert corrida.returncode == 0, corrida.stderr
    assert "Registró 0 vigencias y 0 filas de plan de medición." in corrida.stdout
    assert (filas_de_vigencia(ctx), filas_del_plan(ctx)) == ctx.extras["foto_del_plan"]


@then(parsers.re(r'el guion se detiene con un error que nombra la fila de 5643 en "(?P<periodo>[^"]+)"'))
def _detenido_por_la_fila(ctx: Escenario, periodo: str) -> None:
    corrida = ctx.extras["corrida_plan"]
    assert corrida.returncode == 3, corrida.stdout
    assert f"La fila de 5643 en {periodo} del plan de medición no es la que registra el guion" in corrida.stderr


@then(parsers.re(r'el guion se detiene con (?P<causa>.+)'))
def _detenido(ctx: Escenario, causa: str) -> None:
    corrida = ctx.extras["corrida_plan"]
    assert corrida.returncode == 3, corrida.stdout + corrida.stderr
    esperado = {"el SQLSTATE 22001 del largo": "22001"}.get(causa, causa.strip("«»"))
    assert esperado in corrida.stderr, corrida.stderr


@then(parsers.re(r'huella_ambiental\.sql devuelve la misma huella que antes'))
def _misma_huella(ctx: Escenario) -> None:
    corrida = ctx.extras["corrida_plan"]
    assert corrida.returncode == 0, corrida.stderr
    # El plan de Química sí entró, así que la huella no repite lo de antes por una base sin cambios.
    assert any(f[0] == "2026-1" and f[3] == "5643" for f in filas_del_plan(ctx))
    assert huella_ambiental(ctx) == ctx.extras["huella"]


@then(parsers.re(r'devuelve 1 fila que nombra la asignatura (?P<asignatura>[0-9]+) y el periodo "(?P<periodo>[^"]+)"'))
def _q18_una_fila(ctx: Escenario, asignatura: str, periodo: str) -> None:
    assert ctx.extras["control"] == [(asignatura, periodo)]


@then(parsers.re(r'la fila no trae correos ni códigos de estudiante'))
def _sin_datos_personales(ctx: Escenario) -> None:
    texto = repr(ctx.extras["control"])
    assert "@" not in texto and not re.search(r"\b[0-9]{8}\b", texto)


# US-68. Comprobación de arranque por carrera (T033)

def _arrancar(ctx: Escenario, reglas: str) -> str | None:
    """Arranca la API con ese CONJUNTO_REGLAS y devuelve el mensaje con que se detiene, o None si arranca."""
    ajustes = replace(ctx.api.ajustes, carga=Configuracion(conjunto_reglas=reglas))
    try:
        ctx.api.cliente(ajustes)
    except ConfiguracionDeLaApi as falla:
        return str(falla)
    return None


@when(parsers.re(r'la API arranca con CONJUNTO_REGLAS "(?P<reglas>[^"]+)"'))
def _la_api_arranca(ctx: Escenario, reglas: str) -> None:
    ctx.extras["reglas"] = reglas
    ctx.extras["arranque"] = _arrancar(ctx, reglas)


@then(parsers.re(r'la API no arranca y el mensaje nombra la carrera "(?P<carrera>[A-Z]+)" sin la palabra «Ambiental» '
                 r'\(propuesta\)'))
def _no_arranca(ctx: Escenario, carrera: str) -> None:
    mensaje = ctx.extras["arranque"]
    assert mensaje == f"CONJUNTO_REGLAS {ctx.extras['reglas']} no existe para la carrera {carrera}.", mensaje
    assert "Ambiental" not in mensaje


@then(parsers.re(r'con V1_13 aplicada la API arranca'))
def _arranca_con_v1_13(ctx: Escenario) -> None:
    aplicar(ctx, V1_13)
    assert _arrancar(ctx, ctx.extras["reglas"]) is None
