#!/usr/bin/env bash
# API local en la Mac sobre un clúster desechable, para probar el Front con su proxy de Vite (T036 a T038).
#
# Uso.
#   bash scripts/api_local.sh [--sin-https] [--puerto 8000]
#
# El guion arma con db/pruebas/cluster_desechable.sh un clúster de PostgreSQL 18 desechable, con su socket
# propio y sin TCP, así que nunca toca el clúster de la Mac (localhost:5432) ni abet_sis_med_dev. En ese
# clúster crea la base abet_local con V1_01 a la última migración versionada y las R__, en el orden de
# db/pruebas/correr_pruebas.sh, y corre después la guardia de datos inventados, el rol de la aplicación
# abet_app de db/plataforma/neon/crear_rol_app.sql, sin contraseña, periodo_2026_2_inventado.sql y
# varias_secciones_2026_2_inventado.sql.
#
# Asigna con scripts/asignar_clave.py, por la entrada estándar, una contraseña generada al azar a
# docente410@example.invalid, docente.varias@example.invalid y coordinacion@example.invalid. Las tres se
# escriben solo en un archivo temporal fuera del repositorio, con permisos 600, cuya ruta se imprime, y
# nunca en la pantalla. SESION_SECRETO también se genera al azar y no se imprime.
#
# Después arranca uvicorn en 127.0.0.1 con la conexión del rol de la aplicación. --sin-https deja la cookie
# abet_sesion sin el atributo Secure, porque el navegador no devuelve una cookie Secure por http, y la API
# solo lo admite con una base local y fuera de Vercel (app/configuracion.py). Al cortarlo con Ctrl+C, el
# guion apaga y borra el clúster y el archivo de contraseñas.

set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUERTO=8000
SIN_HTTPS=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --sin-https) SIN_HTTPS=1 ;;
        --puerto) PUERTO="${2:?Falta el número de puerto}"; shift ;;
        *) echo "Opción desconocida $1. Uso: bash scripts/api_local.sh [--sin-https] [--puerto 8000]" >&2; exit 2 ;;
    esac
    shift
done

BD="abet_local"
ROL="abet_app"
USUARIOS=(docente410@example.invalid docente.varias@example.invalid coordinacion@example.invalid)
CLAVES=""

source "$RAIZ/db/pruebas/cluster_desechable.sh"
iniciar_cluster_desechable
if [ -z "${ABET_CLUSTER_DESECHABLE:-}" ]; then
    echo "La API local corre solo en un clúster desechable de la Mac; nada se crea." >&2
    exit 2
fi

terminar() {
    [ -n "$CLAVES" ] && rm -f "$CLAVES"
    detener_cluster_desechable
    echo "Clúster desechable apagado y borrado."
}
trap terminar EXIT
trap 'exit 130' INT TERM

export PGCLIENTENCODING=UTF8
psql_bd() { psql -X -q -v ON_ERROR_STOP=1 -d "$BD" "$@"; }

psql -X -q -v ON_ERROR_STOP=1 -d postgres -c "CREATE DATABASE $BD TEMPLATE template0 ENCODING 'UTF8'"
psql_bd -c "CREATE SCHEMA abet" -c "CREATE SCHEMA acceso"
VERSIONADAS=$(cd "$RAIZ/db/migration" && ls V*__*.sql | sort -t_ -k1,1V -k2,2n)
REPETIBLES=$(cd "$RAIZ/db/migration" && ls R__*.sql | LC_ALL=C sort)
for migracion in $VERSIONADAS $REPETIBLES; do
    PGOPTIONS="-c client_min_messages=warning" psql_bd -1 -f "$RAIZ/db/migration/$migracion" >/dev/null
done
echo "ok migraciones"
psql_bd -f "$RAIZ/db/plataforma/neon/guardia_datos_inventados.sql" >/dev/null
env -u APP_DB_CLAVE psql -X -q -v ON_ERROR_STOP=1 -v rol_app="$ROL" -d "$BD" \
    -f "$RAIZ/db/plataforma/neon/crear_rol_app.sql" >/dev/null
for datos in periodo_2026_2_inventado.sql varias_secciones_2026_2_inventado.sql; do
    psql_bd -f "$RAIZ/db/datos/$datos" >/dev/null
done
echo "ok guardia, rol $ROL sin contraseña y datos inventados de 2026-2"

# El archivo de contraseñas vive en la carpeta temporal del sistema, fuera del repositorio, con permisos 600.
TEMPORAL="${TMPDIR:-/tmp}"
CLAVES="$(umask 077 && mktemp "${TEMPORAL%/}/abet_api_local_claves_XXXXXX")"
DUENO="host=$PGHOST port=$PGPORT dbname=$BD user=postgres"
for correo in "${USUARIOS[@]}"; do
    clave="$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')"
    printf '%s\n' "$clave" | (cd "$RAIZ" && DATABASE_URL="$DUENO" uv run --frozen python scripts/asignar_clave.py \
        --correo "$correo") >/dev/null
    printf '%s %s\n' "$correo" "$clave" >>"$CLAVES"
done
unset clave
echo "ok contraseñas de ${USUARIOS[*]} en $CLAVES (permisos 600; se borra al cortar el guion)"

export DATABASE_URL="host=$PGHOST port=$PGPORT dbname=$BD user=$ROL"
SESION_SECRETO="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
export SESION_SECRETO
export PERIODO_VIGENTE=2026-2 CONJUNTO_REGLAS=R-2026-BORRADOR GUARDIA_DATOS_INVENTADOS=1
if [ "$SIN_HTTPS" -eq 1 ]; then
    export ABET_COOKIE_SIN_SECURE=1
    echo "Aviso: la cookie abet_sesion va sin Secure, solo en este servidor local."
fi

echo "API en http://127.0.0.1:$PUERTO/api (Ctrl+C la detiene y borra el clúster)"
cd "$RAIZ"
uv run --frozen uvicorn app.main:app --host 127.0.0.1 --port "$PUERTO" --no-access-log
