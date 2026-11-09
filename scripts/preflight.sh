#!/usr/bin/env bash
# Revisión previa de cada cambio (docs/devops.md, sección «Controles de cada cambio»).
#
#   bash scripts/preflight.sh                  revisa todos los archivos versionados
#   bash scripts/preflight.sh --staged         revisa lo preparado para el commit (hook pre-commit)
#   bash scripts/preflight.sh --pr <rama-base> revisa el repositorio y el diff del PR contra <rama-base>
#
# Reglas.
#   1. Planillas, exports y respaldos solo dentro de tests/datos_inventados/, más la plantilla del
#      R-17 en su ruta exacta, plantillas/R017_ambiental_general.xlsx.
#   2. En esa carpeta, todo número de 8 dígitos empieza con 99 (códigos inventados). Se revisa cada
#      archivo POR CONTENIDO, sea cual sea su extensión (también los .md, que hoy no dan falsos
#      positivos; si el README llegara a darlos, se excluyen aquí y se anota el motivo).
#        - Un contenedor OLE (firma D0 CF 11 E0 A1 B1 1A E1) falla, porque sus celdas no se pueden
#          revisar, salvo que su SHA-256 esté en OLE_REVISADOS, la lista fija de los contenedores OLE
#          inventados y revisados (hoy solo protegido_410.xlsx, que el generador escribe siempre igual).
#        - Un zip se lee con unzip -p (hojas y cadenas compartidas) y, si unzip no puede abrirlo, por
#          sus bytes.
#        - Todo lo demás (.csv, .tsv, .txt, .xls en texto, UTF-16, Windows-1252, .dat...) pasa por
#          LC_ALL=C tr -d '\000' antes de contar, para que un texto UTF-16 se lea como ASCII.
#      La plantilla del R-17 cumple la misma regla en el texto y en los atributos de texto libre
#      (nombres de hoja, de tabla y de columna, entre otros) de todas sus partes XML y no trae ningún
#      correo. La regla 1 no incluye .txt, porque rompería requirements.txt: un export real renombrado
#      .txt fuera de la carpeta no lo detiene ninguna regla (riesgo residual en docs/devops.md).
#   3. Ningún .env versionado, salvo .env.example.
#   4. Ningún secreto con valor (cadena de conexión con clave, tokens, llaves privadas).
#   5. Todo commit y todo PR que cambia archivos actualiza MEMORIA.md.
#   6. Aviso, sin fallar, si un PR cambia código o configuración y no toca CHANGELOG.md.
#
# Los mensajes nombran el archivo y la regla, nunca el contenido encontrado, para no copiar un
# secreto ni un dato personal en los registros de la CI.
set -euo pipefail

MODO="todo"
BASE=""
case "${1:-}" in
  --staged) MODO="staged" ;;
  --pr) MODO="pr"; BASE="${2:?Falta la rama base, por ejemplo origin/develop}" ;;
  "") ;;
  *) echo "Uso: $0 [--staged | --pr <rama-base>]" >&2; exit 2 ;;
esac

cd "$(git rev-parse --show-toplevel)"

INVENTADOS="tests/datos_inventados/"
PLANTILLA_R17="plantillas/R017_ambiental_general.xlsx"
fallas=0
falla() { echo "::error::$1"; fallas=$((fallas + 1)); }

# core.quotePath=false hace que git nombre tal cual las rutas con caracteres que no son ASCII, como
# «sección.xlsx», que de otro modo pone entre comillas y con escapes octales, y que ninguna regla vería.
if [ "$MODO" = "staged" ]; then
  ARCHIVOS="$(git -c core.quotePath=false diff --cached --name-only --diff-filter=ACMR)"
  GREP_ORIGEN=(--cached)
else
  ARCHIVOS="$(git -c core.quotePath=false ls-files)"
  GREP_ORIGEN=()
fi

# 1. Planillas, exports y respaldos fuera de la carpeta de datos inventados. La plantilla del R-17
#    pasa solo con su ruta exacta, con las mismas mayúsculas.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    "$INVENTADOS"* | "$PLANTILLA_R17") ;;
    *) falla "$f: planilla, export o respaldo fuera de $INVENTADOS y distinto de $PLANTILLA_R17 (regla 1)" ;;
  esac
done <<EOF
$(printf '%s\n' "$ARCHIVOS" | grep -Ei '\.(csv|tsv|xls|xlsx|xlsm|ods|dump|gpg|bak)$' || true)
EOF

# 2. Solo códigos inventados en la carpeta de datos inventados y en la plantilla del R-17.
codigos_reales() {
  # Imprime cuántos números de exactamente 8 dígitos no empiezan con 99, sin mostrarlos. LC_ALL=C y
  # -a hacen que grep lea como texto cualquier byte, también un texto con nulos o en Windows-1252.
  LC_ALL=C grep -aoE '[0-9]+' | LC_ALL=C grep -aE '^[0-9]{8}$' | LC_ALL=C grep -avc '^99' || true
}
# Contenedores OLE inventados y revisados a mano, por SHA-256. Solo protegido_410.xlsx, la forma de un
# libro cifrado que escribe siempre igual scripts/generar_exports_inventados.py y que no trae celdas.
OLE_REVISADOS=(
  "c8eba21bc9c545f6887232d677797ee8083e3a73b7f0a614e5599916d7943b17"
)
sha256_de() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
  else shasum -a 256 "$1" | cut -d' ' -f1; fi
}
primeros_bytes() { # archivo, cantidad: los primeros bytes en hexadecimal minúscula, sin espacios
  head -c "$2" "$1" | od -An -tx1 | tr -d ' \n'
}
codigos_en_archivo() {
  # Imprime cuántos números de 8 dígitos ajenos trae el archivo, leído por contenido.
  local f="$1"
  if [ "$(primeros_bytes "$f" 4)" = "504b0304" ] && unzip -tq "$f" >/dev/null 2>&1; then
    (unzip -p "$f" 'xl/worksheets/*.xml' 'xl/sharedStrings.xml' 2>/dev/null || true) | codigos_reales
  else
    LC_ALL=C tr -d '\000' < "$f" | codigos_reales
  fi
}
es_ole_revisado() {
  local h r
  h="$(sha256_de "$1")"
  for r in "${OLE_REVISADOS[@]}"; do [ "$h" = "$r" ] && return 0; done
  return 1
}
partes_xml() {
  # Contenido de todas las partes XML del libro, con sus relaciones y dibujos VML.
  unzip -p "$1" '*.xml' '*.rels' '*.vml' 2>/dev/null || true
}
ATRIBUTOS_DE_TEXTO='name|displayName|descr|title|tooltip|display|prompt|promptTitle|error|errorTitle|comment|userName|userId|author|codeName|totalsRowLabel'
textos_de_la_plantilla() {
  # Texto de los nodos y valores de los atributos de texto libre, como el nombre de una hoja, de una
  # tabla, de una columna o de un estilo y el autor de una revisión. Los demás atributos traen anchos,
  # colores y medidas, como 33.42578125 o 00808080, que no son códigos.
  partes_xml "$1" | tr '\r\n' '  ' \
    | { grep -oE ">[^<]+<|[[:space:]](${ATRIBUTOS_DE_TEXTO})=\"[^\"]*\"" || true; }
}
revisar_plantilla_r17() {
  # Los números de 8 dígitos se buscan en los textos de la plantilla, y los correos en el contenido
  # entero de sus partes.
  local f="$1" n c
  n="$(textos_de_la_plantilla "$f" | codigos_reales)"
  if [ "${n:-0}" -gt 0 ]; then
    falla "$f: trae $n números de 8 dígitos que no empiezan con 99 (regla 2)"
  fi
  c="$(partes_xml "$f" | { grep -aoE '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+' || true; } | wc -l | tr -d ' ')"
  if [ "${c:-0}" -gt 0 ]; then
    falla "$f: trae $c correos (regla 2)"
  fi
}
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if [ "$f" = "$PLANTILLA_R17" ]; then
    revisar_plantilla_r17 "$f"
    continue
  fi
  if [ ! -f "$f" ]; then continue; fi
  if [ "$(primeros_bytes "$f" 8)" = "d0cf11e0a1b11ae1" ]; then
    if es_ole_revisado "$f"; then continue; fi
    falla "$f: es un contenedor OLE y sus celdas no se pueden revisar (regla 2)"
    continue
  fi
  n="$(codigos_en_archivo "$f")"
  if [ "${n:-0}" -gt 0 ]; then
    falla "$f: trae $n números de 8 dígitos que no empiezan con 99 (regla 2)"
  fi
done <<EOF
$(printf '%s\n' "$ARCHIVOS" | grep -E "^${INVENTADOS}" || true)
$(printf '%s\n' "$ARCHIVOS" | grep -xF "$PLANTILLA_R17" || true)
EOF

# 3. Archivos .env versionados.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  falla "$f: archivo de entorno versionado; solo se admite .env.example (regla 3)"
done <<EOF
$(printf '%s\n' "$ARCHIVOS" | grep -E '(^|/)\.env($|\.)' | grep -vE '(^|/)\.env\.example$' || true)
EOF

# 4. Secretos con valor. git grep -I salta los binarios; cut deja solo archivo y línea.
#    Se excluyen este script y scripts/probar_preflight.sh, que traen los patrones y un
#    secreto falso a propósito para probar la regla.
PATRONES=(
  'postgres(ql)?://[^:/@[:space:]]+:[^@[:space:]]+@'
  'npg_[A-Za-z0-9]{12,}'
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'
  'gh[pousr]_[A-Za-z0-9]{36}'
  'github_pat_[A-Za-z0-9_]{40,}'
  'AKIA[0-9A-Z]{16}'
  '(SECRET|TOKEN|PASSWORD|PASSWD|CLAVE|API_KEY)[A-Z_]*[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9+/_-]{16,}'
)
for p in "${PATRONES[@]}"; do
  while IFS= read -r hallazgo; do
    [ -z "$hallazgo" ] && continue
    falla "$hallazgo: posible secreto con valor (regla 4)"
  done <<EOF
$(git -c core.quotePath=false grep -nIE ${GREP_ORIGEN[@]+"${GREP_ORIGEN[@]}"} -e "$p" -- . ':!scripts/preflight.sh' ':!scripts/probar_preflight.sh' 2>/dev/null | cut -d: -f1,2 || true)
EOF
done

# 5 y 6. MEMORIA.md en cada cambio y aviso de CHANGELOG.md.
revisar_memoria() {
  local cambiados="$1" donde="$2"
  [ -z "$cambiados" ] && return 0
  if ! printf '%s\n' "$cambiados" | grep -qx 'MEMORIA.md'; then
    falla "$donde cambia archivos y no actualiza MEMORIA.md (AGENTS.md, regla 2; regla 5 de este script)"
  fi
}
if [ "$MODO" = "staged" ]; then
  revisar_memoria "$ARCHIVOS" "El commit"
elif [ "$MODO" = "pr" ]; then
  CAMBIADOS="$(git -c core.quotePath=false diff --name-only "$BASE"...HEAD)"
  revisar_memoria "$CAMBIADOS" "El PR"
  if printf '%s\n' "$CAMBIADOS" | grep -vqE '^(MEMORIA\.md|CHANGELOG\.md|README\.md|AGENTS\.md|CLAUDE\.md|docs/|specs/)' \
     && ! printf '%s\n' "$CAMBIADOS" | grep -qx 'CHANGELOG.md'; then
    echo "::warning::El PR cambia código o configuración y no toca CHANGELOG.md (sección «Sin publicar»)"
  fi
fi

if [ "$fallas" -gt 0 ]; then
  echo "Revisión previa: $fallas falla(s). Detalle en docs/devops.md, sección «Controles de cada cambio»."
  exit 1
fi
echo "Revisión previa sin fallas ($MODO)."
