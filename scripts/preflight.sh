#!/usr/bin/env bash
# Revisión previa de cada cambio (docs/devops.md, sección «Controles de cada cambio»).
#
#   bash scripts/preflight.sh                  revisa todos los archivos versionados
#   bash scripts/preflight.sh --staged         revisa lo preparado para el commit (hook pre-commit)
#   bash scripts/preflight.sh --pr <rama-base> revisa el repositorio y el diff del PR contra <rama-base>
#
# Reglas.
#   1. Planillas, exports y respaldos solo dentro de tests/datos_inventados/.
#   2. En esa carpeta, todo número de 8 dígitos empieza con 99 (códigos inventados).
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
fallas=0
falla() { echo "::error::$1"; fallas=$((fallas + 1)); }

if [ "$MODO" = "staged" ]; then
  ARCHIVOS="$(git diff --cached --name-only --diff-filter=ACMR)"
  GREP_ORIGEN=(--cached)
else
  ARCHIVOS="$(git ls-files)"
  GREP_ORIGEN=()
fi

# 1. Planillas, exports y respaldos fuera de la carpeta de datos inventados.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    "$INVENTADOS"*) ;;
    *) falla "$f: planilla, export o respaldo fuera de $INVENTADOS (regla 1)" ;;
  esac
done <<EOF
$(printf '%s\n' "$ARCHIVOS" | grep -Ei '\.(csv|tsv|xls|xlsx|xlsm|ods|dump|gpg|bak)$' || true)
EOF

# 2. Solo códigos inventados en la carpeta de datos inventados.
codigos_reales() {
  # Imprime cuántos números de exactamente 8 dígitos no empiezan con 99, sin mostrarlos.
  grep -oE '[0-9]+' | grep -E '^[0-9]{8}$' | grep -vc '^99' || true
}
while IFS= read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    *.xlsx|*.xlsm)
      n="$( (unzip -p "$f" 'xl/worksheets/*.xml' 'xl/sharedStrings.xml' 2>/dev/null || true) | codigos_reales)" ;;
    *.csv|*.tsv|*.txt)
      n="$(codigos_reales < "$f")" ;;
    *) n=0 ;;
  esac
  if [ "${n:-0}" -gt 0 ]; then
    falla "$f: trae $n números de 8 dígitos que no empiezan con 99 (regla 2)"
  fi
done <<EOF
$(printf '%s\n' "$ARCHIVOS" | grep -E "^${INVENTADOS}" || true)
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
$(git grep -nIE ${GREP_ORIGEN[@]+"${GREP_ORIGEN[@]}"} -e "$p" -- . ':!scripts/preflight.sh' ':!scripts/probar_preflight.sh' 2>/dev/null | cut -d: -f1,2 || true)
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
  CAMBIADOS="$(git diff --name-only "$BASE"...HEAD)"
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
