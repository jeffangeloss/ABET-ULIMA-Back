"""Pasos de los escenarios de US-88 de guia_y_privacidad.feature (spec 008), con pytest-bdd en español (T052).

El .feature manda. Cada escenario arma en tmp_path una copia de prueba, un repositorio de git nuevo con
scripts/preflight.sh del Back y un MEMORIA.md, prepara allí el cambio del «Dado» y corre el guion como lo corre el hook
pre-commit, sin dobles. La copia ignora la configuración de git de la máquina y la variable HUELLAS_CORREOS_PROHIBIDOS
del entorno, que solo pone el escenario que la nombra con la huella del correo inventado real.inventado@example.invalid.
Ningún código fuera del rango 99 se escribe en este archivo, porque la prueba lo arma al correr, salvo los de la lista
cerrada CODIGOS_DE_PRUEBA.

El escenario del contenido actual corre el guion de verdad sobre la copia de trabajo del Back, de solo lectura, y sobre
la del Front cuando ABET_FRONT_RAIZ la nombra. Sin esa variable, la parte del Front queda en su propia integración
continua, que corre scripts/preflight.sh y scripts/probar_preflight.sh del Front con el mismo bloque de reglas, y el
resumen de pytest lo dice. El barrido del historial corre sobre dos copias de prueba con las ramas develop y main, y el
barrido real con la huella del correo real lo corre Jefferson (T052).

Los escenarios de US-87 de este .feature son de Vitest y de Playwright en el Front, salvo el de las tarjetas, que vive
en test_exports_capacitacion_feature.py.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
import shutil
import subprocess
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pytest_bdd import given, parsers, scenario, then, when

Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/guia_y_privacidad.feature"
PREFLIGHT = RAIZ / "scripts" / "preflight.sh"
CORREO_PROHIBIDO = "real.inventado@example.invalid"
AVISO_SIN_HUELLAS = "Sin huellas de correos prohibidos. La regla del correo real no se revisó."
CODIGOS_DE_PRUEBA = ("10000004", "98999999")
# Lo que revisa la regla de ocho cifras en las líneas que agrega un cambio (FR-022, cambio del 2026-11-23).
ALCANCE_OCHO_CIFRAS = ("specs/", "tests/", "e2e/", "docs/", "MEMORIA.md", "CHANGELOG.md")
REGLA_CORREO = "(regla del correo prohibido)"
REGLA_OCHO_CIFRAS = "(regla de ocho cifras)"
REGLA_CAPTURAS = "(regla de las capturas)"
REGLA_MAESTRA = "(regla de la tabla maestra)"
REGLA_TARJETAS = "(regla de las tarjetas)"
REVISADAS = re.compile(r"Regla de ocho cifras: revisó ([0-9]+) líneas? agregadas?")
HISTORIAL = re.compile(r"Historial sin correos prohibidos: ([0-9]+) commits? revisados?")
PALABRA_DE_OCHO = re.compile(r"(?<![0-9A-Za-z])[0-9]{8}(?![0-9A-Za-z])")


def huella(correo: str) -> str:
    """Huella SHA-256 del correo normalizado, sin espacios a los lados y en minúsculas."""
    return hashlib.sha256(correo.strip().lower().encode("utf-8")).hexdigest()


def codigo_ajeno() -> str:
    """Un código de ocho cifras que empieza con 20, armado al correr, que no está en CODIGOS_DE_PRUEBA."""
    return "20" + f"{secrets.randbelow(10**6):06d}"


def huella_con_ocho_cifras() -> str:
    """Una huella SHA-256 inventada que trae ocho cifras seguidas."""
    for i in range(10_000):
        candidata = hashlib.sha256(f"huella inventada {i}".encode()).hexdigest()
        if re.search(r"[0-9]{8}", candidata):
            return candidata
    raise AssertionError("ninguna huella inventada trae ocho cifras seguidas")


# Copia de prueba

@dataclass
class Copia:
    """Repositorio de git en tmp_path con scripts/preflight.sh, aislado de la configuración de la máquina."""

    raiz: Path
    preflight: Path = PREFLIGHT
    entorno: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.entorno = {k: v for k, v in os.environ.items()
                        if not k.startswith("GIT_") and k != "HUELLAS_CORREOS_PROHIBIDOS"}
        self.entorno |= {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        (self.raiz / "scripts").mkdir(parents=True)
        shutil.copy(self.preflight, self.raiz / "scripts" / "preflight.sh")
        (self.raiz / "MEMORIA.md").write_text("# memoria\n", encoding="utf-8")
        (self.raiz / "README.md").write_text("Copia de prueba de docente701@example.invalid.\n", encoding="utf-8")
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "prueba")
        self.git("config", "user.email", "prueba@example.invalid")
        self.git("add", "-A")
        self.git("commit", "-qm", "base", "--no-verify")

    def git(self, *argumentos: str) -> str:
        corrida = subprocess.run(["git", *argumentos], cwd=self.raiz, env=self.entorno, capture_output=True,
                                 text=True, check=False)
        assert corrida.returncode == 0, corrida.stdout + corrida.stderr
        return corrida.stdout

    def escribir(self, ruta: str, contenido: str | bytes) -> None:
        destino = self.raiz / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(contenido, str):
            contenido = contenido.encode("utf-8")
        destino.write_bytes(contenido)

    def agregar_linea(self, ruta: str, linea: str) -> None:
        destino = self.raiz / ruta
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("a", encoding="utf-8") as archivo:
            archivo.write(linea + "\n")

    def preparar(self, *rutas: str) -> None:
        """git add -f de las rutas y una línea más en MEMORIA.md, que el hook exige en cada commit."""
        if "MEMORIA.md" not in rutas:
            self.agregar_linea("MEMORIA.md", "- Entrada de prueba.")
        self.git("add", "-f", "--", *rutas, "MEMORIA.md")

    def reiniciar(self) -> None:
        self.git("reset", "-q", "--hard")
        self.git("clean", "-qfdx")

    def preflight_corre(self, *argumentos: str, huellas: str | None = None) -> subprocess.CompletedProcess[str]:
        entorno = dict(self.entorno)
        if huellas is not None:
            entorno["HUELLAS_CORREOS_PROHIBIDOS"] = huellas
        return subprocess.run(["bash", "scripts/preflight.sh", *argumentos], cwd=self.raiz, env=entorno,
                              capture_output=True, text=True, check=False)


@dataclass
class Cambio:
    """Un cambio preparado del «Dado», con el archivo que el control debe nombrar y la regla que lo detiene."""

    archivo: str
    regla: str
    preparar: Callable[[Copia], None]
    linea: int | None = None
    lineas_en_alcance: int = 0
    no_debe_salir: tuple[str, ...] = ()


@dataclass
class Corrida:
    cambio: Cambio | None
    proceso: subprocess.CompletedProcess[str]

    @property
    def salida(self) -> str:
        return self.proceso.stdout + self.proceso.stderr


def _copia(ctx: Escenario, nombre: str = "copia", preflight: Path = PREFLIGHT) -> Copia:
    copias = ctx.extras.setdefault("copias", {})
    if nombre not in copias:
        copias[nombre] = Copia(ctx.request.getfixturevalue("tmp_path") / nombre, preflight)
    return copias[nombre]


def _cambios(ctx: Escenario) -> list[Cambio]:
    return ctx.extras.setdefault("cambios", [])


def _corridas(ctx: Escenario) -> list[Corrida]:
    corridas = ctx.extras.get("corridas")
    assert corridas, "el escenario no corrió scripts/preflight.sh"
    return corridas


def _lineas_con(salida: str, *textos: str) -> list[str]:
    return [linea for linea in salida.splitlines() if all(texto in linea for texto in textos)]


def _revisadas(salida: str) -> int:
    hallado = REVISADAS.search(salida)
    assert hallado, f"la salida no dice cuántas líneas agregadas revisó la regla de ocho cifras:\n{salida}"
    return int(hallado.group(1))


def _exige_falla_que_nombra(corrida: Corrida, *, con_linea: bool = False) -> None:
    cambio = corrida.cambio
    assert cambio is not None
    assert corrida.proceso.returncode == 1, corrida.salida
    nombre = f"{cambio.archivo}:{cambio.linea}:" if con_linea else cambio.archivo
    assert _lineas_con(corrida.salida, nombre, cambio.regla), (
        f"ninguna línea nombra {nombre} con {cambio.regla}:\n{corrida.salida}")
    for texto in cambio.no_debe_salir:
        assert texto.lower() not in corrida.salida.lower(), "la salida repite lo que encontró"


# Escenarios

@scenario(FEATURE, "El correo prohibido se detecta por su huella sin imprimirlo")
def test_el_correo_prohibido_se_detecta_por_su_huella() -> None:
    """US-88, escenario 1."""


@scenario(FEATURE, "Sin la variable de huellas el control avisa y no falla")
def test_sin_la_variable_de_huellas_el_control_avisa() -> None:
    """US-88, escenario 2."""


@scenario(FEATURE, "Un código de ocho cifras fuera del rango inventado detiene el cambio en specs, pruebas, e2e y docs")
def test_un_codigo_de_ocho_cifras_fuera_del_rango_detiene_el_cambio() -> None:
    """US-88, esquema del escenario 3, con sus ocho ejemplos."""


@scenario(FEATURE, "Una captura o un resultado de Playwright no se versionan")
def test_una_captura_o_un_resultado_de_playwright_no_se_versionan() -> None:
    """US-88, escenario 4."""


@scenario(FEATURE, "La tabla maestra no entra por otro nombre y los archivos legítimos pasan")
def test_la_tabla_maestra_no_entra_por_otro_nombre() -> None:
    """US-88, escenario 5."""


@scenario(FEATURE, "Una tarjeta de profesor dentro del repositorio se rechaza")
def test_una_tarjeta_de_profesor_dentro_del_repositorio_se_rechaza() -> None:
    """US-88, escenario 6."""


@scenario(FEATURE, "La regla nueva no da falsos positivos en el contenido actual")
def test_la_regla_nueva_no_da_falsos_positivos_en_el_contenido_actual() -> None:
    """US-88, escenario 7."""


@scenario(FEATURE, "El historial publicado no trae el correo prohibido")
def test_el_historial_publicado_no_trae_el_correo_prohibido() -> None:
    """US-88, escenario 8."""


# Dado

@given(parsers.parse('la variable HUELLAS_CORREOS_PROHIBIDOS con la huella SHA-256 del correo normalizado "{correo}"'))
def _con_huella(ctx: Escenario, correo: str) -> None:
    assert correo == correo.strip().lower()
    ctx.extras["huellas"] = huella(correo)
    _copia(ctx)


@given("HUELLAS_CORREOS_PROHIBIDOS sin definir")
def _sin_huellas(ctx: Escenario) -> None:
    ctx.extras["huellas"] = None
    _copia(ctx)


@given(parsers.parse('un cambio preparado que agrega "{correo}" a un archivo de specs'))
def _agrega_correo(ctx: Escenario, correo: str) -> None:
    ruta = "specs/008-ciclo-quimica-industrial/aceptacion/contactos.feature"
    assert huella(correo) == ctx.extras["huellas"] and correo != correo.lower()

    def preparar(copia: Copia) -> None:
        copia.escribir(ruta, "# language: es\n# Contactos de la sala.\n# La coordinación escribe a "
                       f"{correo} y a docente701@example.invalid.\n")
        copia.preparar(ruta)

    _cambios(ctx).append(Cambio(ruta, REGLA_CORREO, preparar, linea=3, no_debe_salir=(correo,)))


def _texto_del_ejemplo(ctx: Escenario, texto: str) -> tuple[str, tuple[str, ...]]:
    """La cadena que agrega el ejemplo del esquema y lo que la salida no debe repetir."""
    if texto.startswith("un código de ocho cifras que empieza con 20"):
        codigo = codigo_ajeno()
        return codigo, (codigo,)
    if texto.startswith("una huella SHA-256 de 64 caracteres"):
        valor = huella_con_ocho_cifras()
        assert len(valor) == 64 and re.search(r"[0-9]{8}", valor)
        return f"sha256 {valor}", ()
    literal = re.match(r'"([^"]+)"', texto)
    assert literal, f"ejemplo sin preparar: {texto}"
    return literal.group(1), ()


@given(parsers.re(r'un cambio preparado que agrega (?P<texto>.+) a (?P<archivo>\S*[./]\S*)'))
def _agrega_al_archivo(ctx: Escenario, texto: str, archivo: str) -> None:
    color_versionado = texto.startswith("una línea sin cifras, junto a un color de ocho cifras ya versionado")
    if color_versionado:
        # El gris ARGB de la paleta de la plantilla, armado aquí para no escribirlo, ya está en la rama antes del cambio.
        color = "00" + "808080"
        copia = _copia(ctx)
        copia.agregar_linea(archivo, f'GRIS = "{color}"  # color de la paleta de la plantilla')
        copia.git("add", "-f", "--", archivo)
        copia.git("commit", "-qm", "color versionado", "--no-verify")
        assert PALABRA_DE_OCHO.search((copia.raiz / archivo).read_text(encoding="utf-8"))
        cadena, ocultos = "# Comprobación sin cifras de la paleta.", ()
    else:
        cadena, ocultos = _texto_del_ejemplo(ctx, texto)
        _copia(ctx)
    lineas = 1 if archivo == "MEMORIA.md" else 2

    def preparar(copia: Copia) -> None:
        anteriores = (copia.raiz / archivo).read_text(encoding="utf-8").count("\n") if (copia.raiz / archivo).exists() else 0
        copia.agregar_linea(archivo, f"Valor del ejemplo, {cadena}.")
        assert (copia.raiz / archivo).read_text(encoding="utf-8").count("\n") == anteriores + 1
        copia.preparar(archivo)

    _cambios(ctx).append(Cambio(archivo, REGLA_OCHO_CIFRAS, preparar, lineas_en_alcance=lineas, no_debe_salir=ocultos))


@given(parsers.re(r'un cambio preparado que agrega (?P<captura>e2e/\S+\.png) o (?P<traza>test-results/\S+\.zip)'))
def _agrega_captura(ctx: Escenario, captura: str, traza: str) -> None:
    _copia(ctx)
    png = b"\x89PNG\r\n\x1a\n" + bytes(64)

    def preparar_captura(copia: Copia) -> None:
        copia.escribir(captura, png)
        copia.preparar(captura)

    def preparar_traza(copia: Copia) -> None:
        destino = copia.raiz / traza
        destino.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destino, "w") as z:
            z.writestr("trace.trace", '{"type":"before","title":"P4 de la 701"}\n')
        copia.preparar(traza)

    _cambios(ctx).extend([Cambio(captura, REGLA_CAPTURAS, preparar_captura),
                          Cambio(traza, REGLA_CAPTURAS, preparar_traza)])


@given(parsers.re(r'un cambio preparado que agrega (?P<ruta>docs/\S+\.csv) cuya primera línea trae '
                  r'«(?P<primera>[^»]+)» y «(?P<segunda>[^»]+)»'))
def _agrega_tabla_maestra(ctx: Escenario, ruta: str, primera: str, segunda: str) -> None:
    _copia(ctx)
    encabezado = ("AÑO", "CICLO", "CÓDIGO DEL CURSO", "CURSO", "SO", "PI", "PROFESOR", primera, "SECCIÓN", segunda,
                  "ARCHIVO")
    filas = [",".join(encabezado),
             "2026,1,5643,Química General,6,6.1,Profesor inventado,99000001,701,3,inventado.xlsx"]

    def preparar(copia: Copia) -> None:
        copia.escribir(ruta, "\r\n".join(filas) + "\r\n")
        copia.preparar(ruta)

    _cambios(ctx).append(Cambio(ruta, REGLA_MAESTRA, preparar))


@given(parsers.re(r'un cambio preparado que agrega (?P<ruta>docs/capacitacion/tarjeta_[0-9]+\.md)'))
def _agrega_tarjeta(ctx: Escenario, ruta: str) -> None:
    _copia(ctx)

    def preparar(copia: Copia) -> None:
        copia.escribir(ruta, "# Tarjeta de la sección 701\n\n- Correo: docente701@example.invalid\n"
                       "- Archivo: gc_SINTETICO_20261_5643_701_fullgc_2026-07-15-00-00-00.xlsx\n"
                       "- Contraseña: la entrega la Oficina de Calidad en la sala.\n")
        copia.preparar(ruta)

    _cambios(ctx).append(Cambio(ruta, REGLA_TARJETAS, preparar))


# Cuando

@when(parsers.re(r'corre scripts/preflight\.sh(?P<argumento>(?: --staged)?)'))
def _corre_preflight(ctx: Escenario, argumento: str) -> None:
    copia = _copia(ctx)
    argumentos = argumento.split()
    huellas = ctx.extras.get("huellas")
    corridas = []
    for cambio in _cambios(ctx) or [None]:
        copia.reiniciar()
        if cambio is not None:
            cambio.preparar(copia)
        corridas.append(Corrida(cambio, copia.preflight_corre(*argumentos, huellas=huellas)))
    ctx.extras["corridas"] = corridas


def _repositorios_reales(ctx: Escenario) -> list[Path]:
    repositorios = [RAIZ]
    front = os.environ.get("ABET_FRONT_RAIZ")
    if front:
        repositorios.append(Path(front).resolve())
    else:
        ctx.request.node.user_properties.append(
            ("delegado_a_preflight", "el contenido actual del Front lo revisa su CI con scripts/preflight.sh y "
             "scripts/probar_preflight.sh, con el mismo bloque de reglas; ABET_FRONT_RAIZ lo corre aquí"))
    return repositorios


def _base_del_pr(repositorio: Path) -> str | None:
    corrida = subprocess.run(["git", "rev-parse", "--verify", "-q", "origin/develop^{commit}"], cwd=repositorio,
                             capture_output=True, text=True, check=False)
    return "origin/develop" if corrida.returncode == 0 else None


@when("scripts/preflight.sh corre sobre todo el contenido actual del Back y del Front y con --pr origin/develop sobre "
      "el cambio de la spec 008")
def _corre_sobre_el_contenido_actual(ctx: Escenario) -> None:
    # real.inventado@example.invalid está escrito a propósito en las specs y en las pruebas de la spec 008, así que el
    # contenido actual se revisa con la huella de otro correo inventado, que no está en ningún archivo, o con las
    # huellas de HUELLAS_CORREOS_PROHIBIDOS cuando Jefferson la pone en su entorno.
    entorno = dict(os.environ)
    if not entorno.get("HUELLAS_CORREOS_PROHIBIDOS"):
        entorno["HUELLAS_CORREOS_PROHIBIDOS"] = huella(f"ausente.{secrets.token_hex(6)}@example.invalid")
    corridas = []
    for repositorio in _repositorios_reales(ctx):
        base = _base_del_pr(repositorio)
        modos = [[]] + ([["--pr", base]] if base else [])
        if base is None:
            ctx.request.node.user_properties.append(("sin_casos", f"{repositorio.name} sin origin/develop"))
        for modo in modos:
            proceso = subprocess.run(["bash", "scripts/preflight.sh", *modo], cwd=repositorio, env=entorno,
                                     capture_output=True, text=True, check=False)
            corridas.append((repositorio, modo, proceso))
    ctx.extras["reales"] = corridas


def _historial(copia: Copia, correos: list[str]) -> None:
    """Dos commits en main y uno en develop, con solo correos inventados que no son el prohibido."""
    copia.git("checkout", "-qb", "develop")
    for correo in correos:
        copia.agregar_linea("docs/contactos.md", f"- {correo}")
        copia.git("add", "-A")
        copia.git("commit", "-qm", f"Contacto {correo}", "--no-verify")


@when("corre una vez el barrido del historial de los dos repositorios antes de publicar la spec 008")
def _corre_el_historial(ctx: Escenario) -> None:
    front = os.environ.get("ABET_FRONT_RAIZ")
    preflights = {"back": PREFLIGHT, "front": Path(front) / "scripts" / "preflight.sh" if front else PREFLIGHT}
    ctx.extras["huellas"] = huella(CORREO_PROHIBIDO)
    corridas = []
    for nombre, preflight in preflights.items():
        copia = _copia(ctx, nombre, preflight)
        _historial(copia, ["docente701@example.invalid", "coordinador.quimica@example.invalid"])
        proceso = copia.preflight_corre("--historial", huellas=ctx.extras["huellas"])
        corridas.append((copia, proceso))
    ctx.extras["historial"] = corridas


# Entonces

@then("el control falla y nombra el archivo y su línea")
def _falla_con_linea(ctx: Escenario) -> None:
    for corrida in _corridas(ctx):
        _exige_falla_que_nombra(corrida, con_linea=True)


@then("la salida no repite el correo")
def _no_repite_el_correo(ctx: Escenario) -> None:
    for corrida in _corridas(ctx):
        assert corrida.cambio is not None and corrida.cambio.no_debe_salir
        for correo in corrida.cambio.no_debe_salir:
            assert correo.lower() not in corrida.salida.lower()
            assert huella(correo) not in corrida.salida


@then(parsers.re(r'la salida dice «(?P<texto>[^»]+)» \(propuesta\)'))
def _la_salida_dice(ctx: Escenario, texto: str) -> None:
    assert texto == AVISO_SIN_HUELLAS
    for corrida in _corridas(ctx):
        assert corrida.proceso.returncode == 0, corrida.salida
        assert texto in corrida.proceso.stdout, corrida.salida


@then("el control falla y nombra el archivo")
def _falla_y_nombra(ctx: Escenario) -> None:
    for corrida in _corridas(ctx):
        _exige_falla_que_nombra(corrida)


@then("el control pasa")
def _pasa(ctx: Escenario) -> None:
    for corrida in _corridas(ctx):
        assert corrida.cambio is not None
        assert corrida.proceso.returncode == 0, corrida.salida
        # La regla miró la línea agregada y la aceptó: no basta con que el guion no la conozca.
        assert _revisadas(corrida.salida) == corrida.cambio.lineas_en_alcance, corrida.salida


@then(parsers.re(r'el control falla y nombra (?P<ruta>docs/\S+\.csv)'))
def _falla_y_nombra_la_tabla(ctx: Escenario, ruta: str) -> None:
    for corrida in _corridas(ctx):
        assert corrida.cambio is not None and corrida.cambio.archivo == ruta
        _exige_falla_que_nombra(corrida)


@then("el control falla y nombra la tarjeta")
def _falla_y_nombra_la_tarjeta(ctx: Escenario) -> None:
    for corrida in _corridas(ctx):
        assert corrida.cambio is not None and "tarjeta" in corrida.cambio.archivo
        _exige_falla_que_nombra(corrida)


@then("db/migration/R__vista_tabla_maestra_pi.sql y los .feature que nombran esas columnas pasan")
def _legitimos_pasan(ctx: Escenario) -> None:
    legitimos = ["db/migration/R__vista_tabla_maestra_pi.sql"]
    legitimos += sorted(str(ruta.relative_to(RAIZ)) for ruta in (RAIZ / "specs").rglob("*.feature")
                        if {"CÓDIGO DEL ESTUDIANTE", "CALIFICACIÓN"} <= set(re.findall(
                            r"CÓDIGO DEL ESTUDIANTE|CALIFICACIÓN", ruta.read_text(encoding="utf-8"))))
    assert len(legitimos) >= 2, legitimos
    copia = _copia(ctx)
    copia.reiniciar()
    for ruta in legitimos:
        copia.escribir(ruta, (RAIZ / ruta).read_bytes())
    copia.preparar(*legitimos)
    corrida = copia.preflight_corre("--staged")
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert _revisadas(corrida.stdout) > 0


@then("no encuentra ningún correo prohibido ni ninguna captura")
def _sin_correo_ni_captura(ctx: Escenario) -> None:
    for repositorio, modo, proceso in ctx.extras["reales"]:
        salida = proceso.stdout + proceso.stderr
        assert proceso.returncode == 0, f"{repositorio} {modo}:\n{salida}"
        # La regla del correo corrió con la huella, así que no avisa que no se revisó.
        assert AVISO_SIN_HUELLAS not in salida
        assert REGLA_CORREO not in salida and REGLA_CAPTURAS not in salida
        assert REGLA_MAESTRA not in salida and REGLA_TARJETAS not in salida


def _agregadas_en_alcance(repositorio: Path, base: str) -> int:
    diferencia = subprocess.run(["git", "-c", "core.quotePath=false", "diff", "-U0", "--no-color", "--no-ext-diff",
                                 "--diff-filter=ACMR", f"{base}...HEAD", "--", "specs", "tests", "e2e", "docs",
                                 "MEMORIA.md", "CHANGELOG.md"], cwd=repositorio, capture_output=True, check=True)
    cabecera, total = False, 0
    for linea in diferencia.stdout.split(b"\n"):
        if linea.startswith(b"diff --git "):
            cabecera = True
        elif linea.startswith(b"@@ "):
            cabecera = False
        elif not cabecera and linea.startswith(b"+"):
            total += 1
    return total


@then("la regla de ocho cifras no marca los valores de CODIGOS_DE_PRUEBA ni los colores y decimales que ya estaban "
      "versionados")
def _sin_falsos_positivos(ctx: Escenario) -> None:
    # El contenido actual del Back trae los dos tipos de valor, así que el control limpio no es trivial.
    versionados = subprocess.run(["git", "grep", "-hIoE", "(^|[^0-9A-Za-z])[0-9]{8}([^0-9A-Za-z]|$)", "--",
                                  *ALCANCE_OCHO_CIFRAS], cwd=RAIZ, capture_output=True, text=True, check=False).stdout
    valores = [m.group(0) for m in PALABRA_DE_OCHO.finditer(versionados)]
    assert any(v in CODIGOS_DE_PRUEBA for v in valores)
    assert any(not v.startswith("99") and v not in CODIGOS_DE_PRUEBA for v in valores)
    for repositorio, modo, proceso in ctx.extras["reales"]:
        assert REGLA_OCHO_CIFRAS not in proceso.stdout + proceso.stderr
        if modo:
            # Con --pr la regla revisa cada línea agregada en su alcance, ni una más ni una menos.
            assert _revisadas(proceso.stdout) == _agregadas_en_alcance(repositorio, modo[1]), proceso.stdout


@then("ningún commit de develop ni de main trae un correo con la huella prohibida")
def _historial_limpio(ctx: Escenario) -> None:
    for copia, proceso in ctx.extras["historial"]:
        assert proceso.returncode == 0, proceso.stdout + proceso.stderr
        hallado = HISTORIAL.search(proceso.stdout)
        assert hallado, proceso.stdout
        assert int(hallado.group(1)) == int(copia.git("rev-list", "--count", "develop", "main", "HEAD"))
    # El barrido lee el historial y no solo el contenido: un correo prohibido que un commit de develop agregó y otro
    # quitó lo detiene, nombra ese commit y no lo repite, mientras el contenido actual pasa.
    copia, _ = ctx.extras["historial"][0]
    mezclado = "Real.Inventado@Example.invalid"
    # Al comienzo de la línea, así que el diff lo trae pegado a la marca + y el revert a la marca -.
    copia.agregar_linea("docs/contactos.md", mezclado)
    copia.git("commit", "-qam", "Contacto de la sala", "--no-verify")
    con_correo = copia.git("rev-parse", "--short", "HEAD").strip()
    copia.git("revert", "--no-edit", "HEAD")
    barrido = copia.preflight_corre("--historial", huellas=ctx.extras["huellas"])
    salida = barrido.stdout + barrido.stderr
    assert barrido.returncode == 1, salida
    assert _lineas_con(salida, f"commit {con_correo}:", "(regla del correo prohibido, historial)"), salida
    assert mezclado.lower() not in salida.lower()
    assert copia.preflight_corre(huellas=ctx.extras["huellas"]).returncode == 0
