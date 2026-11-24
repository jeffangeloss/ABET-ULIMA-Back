#!/usr/bin/env bash
# Revisión previa de cada cambio (docs/devops.md, sección «Controles de cada cambio»).
#
#   bash scripts/preflight.sh                  revisa todos los archivos versionados
#   bash scripts/preflight.sh --staged         revisa lo preparado para el commit (hook pre-commit)
#   bash scripts/preflight.sh --pr <rama-base> revisa el repositorio y el diff del PR contra <rama-base>
#   bash scripts/preflight.sh --historial [ref...] barre una vez el historial de develop, main y HEAD (o de las
#                                              referencias dadas) con la regla del correo prohibido
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
# Reglas de privacidad de la spec 008 (US-88, FR-022). El bloque es el mismo en el Back y en el Front, y cada
# regla se nombra por su tema para que los mensajes digan lo mismo en los dos.
#   correo prohibido  Ningún correo cuya huella SHA-256, sin espacios y en minúsculas, esté en la variable
#                     HUELLAS_CORREOS_PROHIBIDOS, que pone Jefferson con huellas separadas por comas o espacios y
#                     nunca con correos en claro. Sin la variable avisa y no falla. Con --historial revisa cada
#                     commit, su mensaje y sus autores.
#   ocho cifras       En las líneas que agrega un cambio (--staged o --pr) dentro de specs/, tests/, e2e/, docs/,
#                     MEMORIA.md y CHANGELOG.md, ningún número de 8 cifras con límite de palabra (una letra o una
#                     cifra al lado lo vuelve parte de otra palabra, como en una huella de 64 caracteres) que no
#                     empiece con 99 y que no esté en la lista cerrada CODIGOS_DE_PRUEBA. El contenido anterior no
#                     se revisa, porque trae colores y decimales de 8 cifras.
#   capturas          Ninguna captura, video, traza ni informe de Playwright.
#   tabla maestra     Ningún archivo tabular (.csv, .tsv, .txt, .dat, .psv, .tab, .xlsx, .xlsm) cuyo encabezado
#                     traiga «CÓDIGO DEL ESTUDIANTE» y «CALIFICACIÓN», con cualquier nombre y en cualquier carpeta.
#   tarjetas          Ninguna tarjeta de profesor (un archivo tarjeta_*, tarjetas.* o dentro de tarjetas/), que
#                     vive fuera de los repositorios.
#
# Los mensajes nombran el archivo y la regla, nunca el contenido encontrado, para no copiar un
# secreto ni un dato personal en los registros de la CI.
set -euo pipefail

MODO="todo"
BASE=""
REFERENCIAS=()
case "${1:-}" in
  --staged) MODO="staged" ;;
  --pr) MODO="pr"; BASE="${2:?Falta la rama base, por ejemplo origin/develop}" ;;
  --historial) MODO="historial"; shift; REFERENCIAS=("$@") ;;
  "") ;;
  *) echo "Uso: $0 [--staged | --pr <rama-base> | --historial [ref...]]" >&2; exit 2 ;;
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

# Reglas de privacidad de la spec 008 (US-88, FR-022). Este bloque es el mismo en el Back y en el Front.
CORREO_RE='[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+([.][A-Za-z0-9-]+)+'
# Lista cerrada de los códigos ajenos al rango 99 que usan las pruebas de la guardia de la spec 001 (FR-022).
CODIGOS_DE_PRUEBA=(10000004 98999999)
ALCANCE_OCHO_CIFRAS=(specs tests e2e docs MEMORIA.md CHANGELOG.md)
AVISO_SIN_HUELLAS="Sin huellas de correos prohibidos. La regla del correo real no se revisó."

sha256_texto() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum | cut -d' ' -f1
  else shasum -a 256 | cut -d' ' -f1; fi
}
# Una huella por línea, en minúsculas. Nunca se imprimen.
HUELLAS="$(printf '%s\n' "${HUELLAS_CORREOS_PROHIBIDOS:-}" | tr ',;\t\r' '\n\n\n\n' | tr ' ' '\n' | sed '/^$/d' | tr 'A-F' 'a-f')"
huellas_validas() {
  # Falla sin repetir el valor si la variable trae algo que no es una huella, como un correo en claro.
  if printf '%s\n' "$HUELLAS" | grep -qvE '^[0-9a-f]{64}$'; then
    falla "HUELLAS_CORREOS_PROHIBIDOS trae un valor que no es una huella SHA-256 en hexadecimal (regla del correo prohibido)"
    return 1
  fi
}
revisar_correos() { # líneas «origen:correo», sufijo del motivo
  # Calcula la huella de cada correo distinto, normalizado en minúsculas, y falla una vez por cada origen que trae
  # uno prohibido. El mensaje nombra el origen y nunca el correo.
  local lineas="$1" motivo="$2" correo origen
  [ -z "$lineas" ] && return 0
  # Los signos + y - del comienzo son la marca de una línea de un diff, no parte del correo.
  lineas="$(printf '%s\n' "$lineas" | LC_ALL=C sed -E 's/:[-+]+([^:]*)$/:\1/')"
  while IFS= read -r correo; do
    [ -z "$correo" ] && continue
    printf '%s\n' "$HUELLAS" | grep -qxF "$(printf '%s' "$correo" | sha256_texto)" || continue
    while IFS= read -r origen; do
      [ -n "$origen" ] && falla "$origen: trae un correo prohibido por su huella ($motivo)"
    done <<EOF_ORIGENES
$(printf '%s\n' "$lineas" | LC_ALL=C awk -v c="$correo" '{
  e = $0; sub(/.*:/, "", e); o = substr($0, 1, length($0) - length(e) - 1)
  if (tolower(e) == c && !(o in visto)) { visto[o] = 1; print o } }')
EOF_ORIGENES
  done <<EOF_CORREOS
$(printf '%s\n' "$lineas" | sed 's/.*://' | LC_ALL=C tr 'A-Z' 'a-z' | sort -u)
EOF_CORREOS
}
leer() { # archivo: su contenido en el índice con --staged y en la copia de trabajo en los otros modos
  if [ "$MODO" = "staged" ]; then git cat-file blob ":$1" 2>/dev/null || true
  else cat -- "$1" 2>/dev/null || true; fi
}

# Barrido del historial, una vez antes de publicar (US-88). Revisa cada commit de develop, main y HEAD, o de las
# referencias dadas, con su mensaje, sus autores y su diff, y termina sin correr las demás reglas.
if [ "$MODO" = "historial" ]; then
  if [ -z "$HUELLAS" ]; then
    echo "Sin huellas de correos prohibidos. El historial no se revisó."
    exit 2
  fi
  huellas_validas || { echo "Revisión del historial: 1 falla(s)."; exit 1; }
  if [ "${#REFERENCIAS[@]}" -eq 0 ]; then
    for r in develop main; do
      if git rev-parse --verify -q "origin/$r^{commit}" >/dev/null; then REFERENCIAS+=("origin/$r")
      elif git rev-parse --verify -q "$r^{commit}" >/dev/null; then REFERENCIAS+=("$r"); fi
    done
    [ "${#REFERENCIAS[@]}" -eq 0 ] && { echo "No se encontraron develop ni main." >&2; exit 2; }
    REFERENCIAS+=(HEAD)
  fi
  total="$(git rev-list --count "${REFERENCIAS[@]}")"
  revisar_correos "$(git -c core.quotePath=false log -p --no-color --no-ext-diff \
      --format='%x01%h%n%an <%ae>%n%cn <%ce>%n%B' "${REFERENCIAS[@]}" | LC_ALL=C awk -v re="$CORREO_RE" '
    /^\001/ { c = substr($0, 2); next }
    { s = $0; while (match(s, re)) { print "commit " c ":" substr(s, RSTART, RLENGTH); s = substr(s, RSTART + RLENGTH) } }')" \
    "regla del correo prohibido, historial"
  if [ "$fallas" -gt 0 ]; then
    echo "Revisión del historial: $fallas falla(s) en $total commits de ${REFERENCIAS[*]}."
    exit 1
  fi
  echo "Historial sin correos prohibidos: $total commits revisados de ${REFERENCIAS[*]}."
  exit 0
fi

# Correo prohibido, en todo el contenido que revisa el modo, con su archivo y su línea.
if [ -z "$HUELLAS" ]; then
  echo "$AVISO_SIN_HUELLAS"
elif huellas_validas; then
  revisar_correos "$(git -c core.quotePath=false grep -nIoE ${GREP_ORIGEN[@]+"${GREP_ORIGEN[@]}"} -e "$CORREO_RE" -- . 2>/dev/null || true)" \
    "regla del correo prohibido"
fi

# Ocho cifras, solo en las líneas que agrega el cambio. Una palabra es una racha de letras y cifras ASCII, así que
# una huella de 64 caracteres, una fecha con guiones y una cifra de 7 dígitos no son códigos.
if [ "$MODO" = "staged" ] || [ "$MODO" = "pr" ]; then
  if [ "$MODO" = "staged" ]; then RANGO=(--cached); else RANGO=("$BASE...HEAD"); fi
  RESULTADO="$(git -c core.quotePath=false diff "${RANGO[@]}" -U0 --no-color --no-ext-diff --diff-filter=ACMR \
      -- "${ALCANCE_OCHO_CIFRAS[@]}" | LC_ALL=C awk -v lista="${CODIGOS_DE_PRUEBA[*]}" '
    BEGIN { split(lista, l, " "); for (i in l) prueba[l[i]] = 1 }
    /^diff --git / { cabecera = 1; next }
    cabecera && /^\+\+\+ / { f = substr($0, 5); sub(/^b\//, "", f); sub(/\t$/, "", f); next }
    /^@@ / { cabecera = 0; match($0, /\+[0-9]+/); n = substr($0, RSTART + 1, RLENGTH - 1) + 0; next }
    cabecera { next }
    /^\+/ {
      revisadas++; s = substr($0, 2); k = 0
      while (match(s, /[0-9A-Za-z]+/)) {
        t = substr(s, RSTART, RLENGTH); s = substr(s, RSTART + RLENGTH)
        if (length(t) == 8 && t ~ /^[0-9]+$/ && t !~ /^99/ && !(t in prueba)) k++
      }
      if (k > 0) print k "\t" f ":" n
      n++
    }
    END { print "#revisadas\t" revisadas + 0 }')"
  revisadas=0
  while IFS="$(printf '\t')" read -r cuenta origen; do
    [ -z "$cuenta" ] && continue
    if [ "$cuenta" = "#revisadas" ]; then revisadas="$origen"; continue; fi
    falla "$origen: trae $cuenta números de 8 cifras fuera del rango 99 y de CODIGOS_DE_PRUEBA (regla de ocho cifras)"
  done <<EOF
$RESULTADO
EOF
  if [ "$revisadas" = "1" ]; then lineas="línea agregada"; else lineas="líneas agregadas"; fi
  echo "Regla de ocho cifras: revisó $revisadas $lineas en specs/, tests/, e2e/, docs/, MEMORIA.md y CHANGELOG.md."
fi

# Capturas, videos, trazas e informes de Playwright.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  falla "$f: captura, video, traza o informe de Playwright versionado (regla de las capturas)"
done <<EOF
$(printf '%s\n' "$ARCHIVOS" | grep -Ei '(^|/)(test-results|playwright-report|blob-report|capturas)/|(^|/)trace\.zip$|^e2e/.*\.(png|jpe?g|webp|gif|bmp|webm|mp4|zip)$' || true)
EOF

# Tabla maestra por su encabezado, con cualquier nombre y en cualquier carpeta. En un texto se leen las primeras 20
# líneas no vacías (sin nulos, para leer un UTF-16 como ASCII, y sin el BOM), porque un export puede traer una línea de
# título antes del encabezado (cambio del 2026-11-23 de FR-022), y en un libro, sus cadenas compartidas y su primera hoja.
encabezado_tabular() {
  local f="$1" t
  case "$f" in
    *.[xX][lL][sS][xX] | *.[xX][lL][sS][mM])
      t="$(mktemp)"
      leer "$f" > "$t"
      { unzip -p "$t" 'xl/sharedStrings.xml' 'xl/worksheets/sheet1.xml' 2>/dev/null | LC_ALL=C tr -d '\000'; } || true
      rm -f "$t" ;;
    *) { leer "$f" | head -c 65536 | LC_ALL=C tr -d '\000' | LC_ALL=C tr '\r' '\n' | LC_ALL=C sed $'s/^\xef\xbb\xbf//' \
           | LC_ALL=C grep -av '^[[:space:]]*$' | head -n 20; } 2>/dev/null || true ;;
  esac
}
while IFS= read -r f; do
  [ -z "$f" ] && continue
  # La plantilla del R-17 del Back nombra esas columnas en su tabla, y la regla 2 ya revisa sus textos y sus correos.
  [ "$f" = "${PLANTILLA_R17:-}" ] && continue
  encabezado="$(encabezado_tabular "$f")"
  if printf '%s' "$encabezado" | LC_ALL=C grep -aiqE 'C.{0,2}DIGO[ _]+DEL[ _]+ESTUDIANTE' \
     && printf '%s' "$encabezado" | LC_ALL=C grep -aiqE 'CALIFICACI.{0,2}N'; then
    falla "$f: archivo tabular con el encabezado de la tabla maestra (regla de la tabla maestra)"
  fi
done <<EOF
$(printf '%s\n' "$ARCHIVOS" | grep -Ei '\.(csv|tsv|txt|dat|psv|tab|xlsx|xlsm)$' || true)
EOF

# Tarjetas de profesor, por su nombre. Un componente o una prueba con «tarjeta» en el nombre no es una tarjeta.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  falla "$f: tarjeta de profesor dentro del repositorio (regla de las tarjetas)"
done <<EOF
$(printf '%s\n' "$ARCHIVOS" | grep -Ei '(^|/)tarjetas?([_ .-][^/]*)?$|(^|/)tarjetas/' \
  | grep -Evi '\.(ts|tsx|js|jsx|mjs|cjs|py|sh|css|sql|feature)$' || true)
EOF

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
