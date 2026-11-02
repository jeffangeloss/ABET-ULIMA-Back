#!/usr/bin/env bash
# Prueba scripts/preflight.sh y el hook scripts/recordar_memoria.sh en un repositorio temporal, con
# casos que deben pasar y casos que deben fallar. Lo corre el check «pruebas» de la CI.
#   bash scripts/probar_preflight.sh
# Solo usa bash, git y python3 de la biblioteca estándar; los archivos de prueba se generan aquí
# con datos inventados y un secreto falso que nunca debe aparecer en la salida.
set -u

SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
PREFLIGHT="$SCRIPTS/preflight.sh"
PLANTILLA_REAL="$SCRIPTS/../plantillas/R017_ambiental_general.xlsx"
GITIGNORE="$SCRIPTS/../.gitignore"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
cd "$T"
git init -q
git config user.name prueba
git config user.email prueba@example.invalid
mkdir -p scripts tests/datos_inventados
cp "$PREFLIGHT" scripts/preflight.sh
cp "$SCRIPTS/recordar_memoria.sh" scripts/recordar_memoria.sh
echo "# memoria" > MEMORIA.md
echo "x" > README.md
git add -A
git commit -qm base --no-verify
RAMA_BASE="$(git rev-parse --abbrev-ref HEAD)"

xlsx() { # ruta, código
  python3 - "$1" "$2" <<'PY'
import sys, zipfile
ruta, codigo = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(ruta, "w") as z:
    z.writestr("xl/worksheets/sheet1.xml",
               '<worksheet><sheetData><row r="2"><c r="C2"><v>%s</v></c>'
               '<c r="Y2"><v>3</v></c></row></sheetData></worksheet>' % codigo)
    z.writestr("xl/sharedStrings.xml", "<sst/>")
PY
}

plantilla() { # ruta, variante (limpia, codigo_en_hoja, codigo_en_propiedades, codigo_en_nombre_de_hoja o correo)
  # Libro mínimo con la forma de la plantilla del R-17. Su columna D mide 33.42578125, un ancho con
  # 8 decimales que no es un código, como los de la plantilla real, y su paleta trae el color
  # 00808080, que tiene 8 cifras y tampoco lo es.
  python3 - "$1" "$2" <<'PY'
import sys, zipfile
ruta, variante = sys.argv[1], sys.argv[2]
valor = {"codigo_en_hoja": "20231234", "correo": "alguien@example.invalid"}.get(variante, "Código:")
autor = "20231234" if variante == "codigo_en_propiedades" else "ABET_SIS_MED"
hoja = "20231234" if variante == "codigo_en_nombre_de_hoja" else "Cursos de Carrera"
with zipfile.ZipFile(ruta, "w") as z:
    z.writestr("xl/workbook.xml", '<workbook><sheets><sheet name="%s" sheetId="1"/></sheets></workbook>' % hoja)
    z.writestr("xl/styles.xml",
               '<styleSheet><colors><indexedColors><rgbColor rgb="00808080"/></indexedColors></colors></styleSheet>')
    z.writestr("xl/worksheets/sheet1.xml",
               '<worksheet><cols><col min="4" max="4" width="33.42578125"/></cols><sheetData><row r="8">'
               '<c r="B8" t="inlineStr"><is><t>%s</t></is></c></row></sheetData></worksheet>' % valor)
    z.writestr("docProps/core.xml",
               '<cp:coreProperties xmlns:cp="c" xmlns:dc="d"><dc:creator>%s</dc:creator></cp:coreProperties>' % autor)
PY
}

bien=0
mal=0
limpiar() {
  git checkout -q "$RAMA_BASE" 2>/dev/null
  git reset -q --hard
  git clean -qfdx
  mkdir -p tests/datos_inventados
}
caso() { # nombre, esperado (0 pasa, 1 falla), comando
  local nombre="$1" esperado="$2" salida rc real
  shift 2
  salida="$("$@" 2>&1)"
  rc=$?
  real=$([ "$rc" -eq 0 ] && echo 0 || echo 1)
  if [ "$real" = "$esperado" ] && ! printf '%s' "$salida" | grep -q 'secretoFalso'; then
    bien=$((bien + 1)); echo "bien  $nombre"
  else
    mal=$((mal + 1)); echo "MAL   $nombre (salida $rc)"; printf '%s\n' "$salida" | sed 's/^/      /'
  fi
  limpiar
}
caso_por() { # nombre, regla que debe nombrar la salida (por ejemplo «regla 2»), comando que debe fallar
  local nombre="$1" regla="$2" salida rc
  shift 2
  salida="$("$@" 2>&1)"
  rc=$?
  if [ "$rc" -ne 0 ] && printf '%s' "$salida" | grep -qF "($regla)" && ! printf '%s' "$salida" | grep -q 'secretoFalso'; then
    bien=$((bien + 1)); echo "bien  $nombre"
  else
    mal=$((mal + 1)); echo "MAL   $nombre (salida $rc, se esperaba una falla por la $regla)"; printf '%s\n' "$salida" | sed 's/^/      /'
  fi
  limpiar
}

caso "commit con MEMORIA.md pasa" 0 bash -c 'echo y >> README.md; echo e >> MEMORIA.md; git add -A; bash scripts/preflight.sh --staged'
caso "commit sin MEMORIA.md falla" 1 bash -c 'echo y >> README.md; git add -A; bash scripts/preflight.sh --staged'
caso "xlsx fuera de datos_inventados falla" 1 bash -c "$(declare -f xlsx); xlsx export.xlsx 99000001; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged"
caso "xlsx con código 99 en datos_inventados pasa" 0 bash -c "$(declare -f xlsx); xlsx tests/datos_inventados/e.xlsx 99000001; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged"
caso "xlsx con código que no empieza con 99 falla" 1 bash -c "$(declare -f xlsx); xlsx tests/datos_inventados/r.xlsx 20231234; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged"
caso "csv con 99000001,99000002 pasa" 0 bash -c 'printf "codigo\n99000001,99000002\n" > tests/datos_inventados/a.csv; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged'
caso "csv con 99000001,20231234 falla" 1 bash -c 'printf "codigo\n99000001,20231234\n" > tests/datos_inventados/a.csv; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged'
caso ".env versionado falla" 1 bash -c 'echo "A=1" > .env; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged'
caso ".env.example sin valores pasa" 0 bash -c 'echo "DATABASE_URL=" > .env.example; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged'
caso "cadena de conexión con clave falla sin mostrarla" 1 bash -c 'echo "url = postgres://usuario:secretoFalso@ep-x.sa-east-1.aws.neon.tech/neondb" > conf.txt; echo e >> MEMORIA.md; git add -A; bash scripts/preflight.sh --staged'
caso "token con valor falla sin mostrarlo" 1 bash -c 'echo "SONAR_TOKEN=secretoFalsoAAAAAAAAAAAAAA" > conf.txt; echo e >> MEMORIA.md; git add -A; bash scripts/preflight.sh --staged'
caso "referencia a un secreto de Actions pasa" 0 bash -c 'echo "SONAR_TOKEN: \${{ secrets.SONAR_TOKEN }}" > w.yml; echo e >> MEMORIA.md; git add -A; bash scripts/preflight.sh --staged'
caso "PR sin MEMORIA.md falla" 1 bash -c "git checkout -qb feat/x; echo y >> README.md; git commit -qam c --no-verify; bash scripts/preflight.sh --pr $RAMA_BASE"
caso "PR con MEMORIA.md pasa" 0 bash -c "git checkout -qb feat/y; echo y >> README.md; echo e >> MEMORIA.md; git commit -qam c --no-verify; bash scripts/preflight.sh --pr $RAMA_BASE"
caso "repositorio limpio en modo completo pasa" 0 bash scripts/preflight.sh
caso "hook de memoria: repositorio limpio no bloquea" 0 bash -c 'printf "{}" | CLAUDE_PROJECT_DIR="$PWD" bash scripts/recordar_memoria.sh'
caso "hook de memoria: cambio sin MEMORIA.md bloquea" 1 bash -c 'echo y >> README.md; printf "{}" | CLAUDE_PROJECT_DIR="$PWD" bash scripts/recordar_memoria.sh'
caso "hook de memoria: cambio con MEMORIA.md no bloquea" 0 bash -c 'echo y >> README.md; echo e >> MEMORIA.md; printf "{}" | CLAUDE_PROJECT_DIR="$PWD" bash scripts/recordar_memoria.sh'
caso "hook de memoria: no bloquea dos veces seguidas" 0 bash -c 'echo y >> README.md; printf "{\"stop_hook_active\": true}" | CLAUDE_PROJECT_DIR="$PWD" bash scripts/recordar_memoria.sh'

# Plantilla del R-17 (T034). Es la única planilla admitida fuera de tests/datos_inventados/, solo en su
# ruta exacta, y la regla 2 revisa el texto de todas sus partes y sus correos.
CON_PLANTILLA="$(declare -f plantilla); mkdir -p plantillas docs"
caso "plantilla del R-17 en su ruta, con un ancho de 8 decimales, pasa" 0 bash -c "$CON_PLANTILLA; plantilla plantillas/R017_ambiental_general.xlsx limpia; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged"
caso "plantilla real de plantillas/ en su ruta pasa" 0 bash -c "mkdir -p plantillas; cp '$PLANTILLA_REAL' plantillas/; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged"
caso "modo completo con la plantilla versionada pasa" 0 bash -c "$CON_PLANTILLA; git checkout -qb plantilla; plantilla plantillas/R017_ambiental_general.xlsx limpia; echo e >> MEMORIA.md; git add -f -A; git commit -qm p --no-verify; bash scripts/preflight.sh"
caso_por "otro .xlsx en plantillas/ falla" "regla 1" bash -c "$CON_PLANTILLA; plantilla plantillas/R017_capstone.xlsx limpia; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged"
caso_por "la plantilla con otro nombre falla" "regla 1" bash -c "$CON_PLANTILLA; plantilla plantillas/R017_ambiental_general_v2.xlsx limpia; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged"
caso_por "la plantilla con otras mayúsculas falla" "regla 1" bash -c "$CON_PLANTILLA; plantilla plantillas/r017_ambiental_general.xlsx limpia; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged"
caso_por "la plantilla en otra carpeta falla" "regla 1" bash -c "$CON_PLANTILLA; plantilla docs/R017_ambiental_general.xlsx limpia; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged"
caso_por "plantilla con un código que no empieza con 99 falla" "regla 2" bash -c "$CON_PLANTILLA; plantilla plantillas/R017_ambiental_general.xlsx codigo_en_hoja; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged"
caso_por "plantilla con un código en sus propiedades falla" "regla 2" bash -c "$CON_PLANTILLA; plantilla plantillas/R017_ambiental_general.xlsx codigo_en_propiedades; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged"
caso_por "plantilla con un código en el nombre de una hoja falla" "regla 2" bash -c "$CON_PLANTILLA; plantilla plantillas/R017_ambiental_general.xlsx codigo_en_nombre_de_hoja; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged"
caso_por "plantilla con un correo falla" "regla 2" bash -c "$CON_PLANTILLA; plantilla plantillas/R017_ambiental_general.xlsx correo; echo e >> MEMORIA.md; git add -f -A; bash scripts/preflight.sh --staged"
caso "gitignore no ignora la plantilla en su ruta" 0 bash -c "cp '$GITIGNORE' .gitignore; ! git check-ignore -q plantillas/R017_ambiental_general.xlsx"
caso "gitignore ignora otro .xlsx en plantillas/" 0 bash -c "cp '$GITIGNORE' .gitignore; git check-ignore -q plantillas/R017_capstone.xlsx"

echo "Prueba de la revisión previa y del hook de memoria: $bien bien, $mal mal."
[ "$mal" -eq 0 ]
