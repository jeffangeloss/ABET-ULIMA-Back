#!/usr/bin/env bash
# Prueba scripts/preflight.sh en un repositorio temporal con casos que deben pasar y casos que
# deben fallar. Lo corre el check «pruebas» de la CI antes de la revisión previa.
#   bash scripts/probar_preflight.sh
# Solo usa bash, git y python3 de la biblioteca estándar; los archivos de prueba se generan aquí
# con datos inventados y un secreto falso que nunca debe aparecer en la salida.
set -u

PREFLIGHT="$(cd "$(dirname "$0")" && pwd)/preflight.sh"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
cd "$T"
git init -q
git config user.name prueba
git config user.email prueba@example.invalid
mkdir -p scripts tests/datos_inventados
cp "$PREFLIGHT" scripts/preflight.sh
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

bien=0
mal=0
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
  git checkout -q "$RAMA_BASE" 2>/dev/null
  git reset -q --hard
  git clean -qfdx
  mkdir -p tests/datos_inventados
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

echo "Prueba de la revisión previa: $bien bien, $mal mal."
[ "$mal" -eq 0 ]
