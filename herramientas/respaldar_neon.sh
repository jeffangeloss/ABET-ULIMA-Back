#!/usr/bin/env bash
# Respaldo de la base en Neon con pg_dump. Lo corre cada día .github/workflows/respaldo_neon.yml y también
# se puede correr a mano desde la Mac.
#   1. Vuelca en formato custom de pg_dump el esquema abet (tablas, vistas, datos e historial de Flyway) y, desde
#      V1_09, el esquema acceso con los usuarios y sus secciones, sin los datos de credencial, sesion,
#      intento_fallido ni codigo_acceso.
#   2. Comprueba que el archivo se puede leer con pg_restore --list, que trae el historial de Flyway y los datos
#      de las tablas, y que esas cuatro tablas de acceso llegan sin datos.
#   3. Lo cifra con gpg (AES-256, clave simétrica) y borra la copia sin cifrar, porque la base puede
#      tener datos personales.
#   4. Escribe la huella SHA-256 del archivo cifrado para comprobar su integridad al restaurar.
#
# Uso: herramientas/respaldar_neon.sh <carpeta_de_salida>
#
# Conexión por variables de entorno:
#   NEON_HOST y NEON_DB, los mismos del entorno neon de flyway.toml (host de la conexión directa, sin "-pooler",
#   porque pg_dump no funciona bien detrás del repartidor de conexiones en modo transacción).
#   NEON_DB_USER y NEON_DB_PASSWORD, que en el respaldo diario son los del usuario abet_respaldo, de solo lectura,
#   creado con db/plataforma/neon/crear_roles_lectura.sql. El dueño de la base también sirve desde la Mac.
# Cifrado:
#   RESPALDO_CLAVE    frase de cifrado de gpg. Nunca va en un archivo del repositorio.
# Opcionales:
#   PG_DUMP, PG_RESTORE, GPG   rutas de los programas (por defecto, los del PATH)
#   PG_MAYOR                   versión mayor que deben tener pg_dump y pg_restore (por defecto 16). Debe ser la del
#                              servidor y la del pg_restore con que se va a restaurar, porque un pg_restore más viejo
#                              no lee el archivo de un pg_dump más nuevo
#   PGSSLMODE, PGSSLROOTCERT   por defecto verify-full y system, que validan el certificado de Neon con los
#                              certificados raíz del sistema (libpq 16 o posterior)
set -euo pipefail

SALIDA="${1:?Uso: herramientas/respaldar_neon.sh <carpeta_de_salida>}"
PG_DUMP="${PG_DUMP:-pg_dump}"
PG_RESTORE="${PG_RESTORE:-pg_restore}"
GPG="${GPG:-gpg}"
PG_MAYOR="${PG_MAYOR:-16}"

: "${NEON_HOST:?Falta NEON_HOST}" "${NEON_DB:?Falta NEON_DB}" "${NEON_DB_USER:?Falta NEON_DB_USER}"
: "${NEON_DB_PASSWORD:?Falta NEON_DB_PASSWORD}" "${RESPALDO_CLAVE:?Falta RESPALDO_CLAVE}"

# libpq lee la conexión de estas variables, así que la contraseña no aparece en la línea de comandos.
export PGHOST="$NEON_HOST" PGDATABASE="$NEON_DB" PGUSER="$NEON_DB_USER" PGPASSWORD="$NEON_DB_PASSWORD"
export PGSSLMODE="${PGSSLMODE:-verify-full}" PGSSLROOTCERT="${PGSSLROOTCERT:-system}"
export PGCONNECT_TIMEOUT="${PGCONNECT_TIMEOUT:-30}" PGAPPNAME="respaldo_abet"

for programa in "$PG_DUMP" "$PG_RESTORE"; do
    "$programa" --version | grep -Eq " ${PG_MAYOR}\." || { echo "Hace falta $programa en la versión mayor ${PG_MAYOR}" >&2; exit 1; }
done

umask 077
mkdir -p "$SALIDA"
SELLO="$(date -u +%Y%m%dT%H%M%SZ)"
BASE="$SALIDA/abet_${NEON_DB}_${SELLO}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Desde V1_09, abet.carga.subida_por tiene una clave foránea hacia acceso.usuario_autorizado, así que un volcado
# solo de abet ya no se restaura en una base vacía. Por eso el respaldo lleva también acceso, aunque de las tablas
# de credenciales, sesiones, intentos fallidos y códigos guarda solo la definición. Sin --strict-names, pg_dump
# ignora un --schema que no encuentra mientras otro coincida, así que antes de V1_09 el volcado trae solo abet.
ACCESO_SIN_DATOS=(credencial sesion intento_fallido codigo_acceso)
ESQUEMAS=(--schema=abet --schema=acceso)
for tabla in "${ACCESO_SIN_DATOS[@]}"; do
    ESQUEMAS+=("--exclude-table-data=acceso.$tabla")
done

echo "== Volcado del esquema abet y, si existe, del esquema acceso"
"$PG_DUMP" --format=custom --compress=9 "${ESQUEMAS[@]}" --no-owner --no-privileges --file="$TMP/respaldo.dump"

echo "== Comprobación del archivo"
"$PG_RESTORE" --list "$TMP/respaldo.dump" > "$TMP/indice.txt"
grep -q 'TABLE DATA abet flyway_schema_history' "$TMP/indice.txt" || { echo "El respaldo no trae el historial de Flyway" >&2; exit 1; }
TABLAS="$(grep -c 'TABLE DATA abet ' "$TMP/indice.txt" || true)"
echo "ok el archivo se lee y trae los datos de ${TABLAS} tablas de abet, incluido el historial de Flyway"
if grep -q ' SCHEMA - acceso ' "$TMP/indice.txt"; then
    # Cada tabla de la lista debe llegar con su definición y sin sus datos. Si una cambia de nombre, el patrón de
    # exclusión deja de coincidir, y el respaldo se detiene antes de cifrar en lugar de guardar sus datos.
    for tabla in "${ACCESO_SIN_DATOS[@]}"; do
        grep -q " TABLE acceso $tabla " "$TMP/indice.txt" || { echo "El respaldo no trae la tabla acceso.$tabla; hay que revisar ACCESO_SIN_DATOS" >&2; exit 1; }
        if grep -q " TABLE DATA acceso $tabla " "$TMP/indice.txt"; then echo "El respaldo trae los datos de acceso.$tabla" >&2; exit 1; fi
        echo "ok acceso.$tabla llega con su definición y sin datos"
    done
    grep -q 'TABLE DATA acceso usuario_autorizado ' "$TMP/indice.txt" || { echo "El respaldo no trae los usuarios de acceso" >&2; exit 1; }
    echo "ok trae los datos de $(grep -c 'TABLE DATA acceso ' "$TMP/indice.txt" || true) tablas de acceso, entre ellas usuario_autorizado"
else
    echo "ok la base no tiene el esquema acceso, así que el respaldo trae solo abet"
fi

echo "== Cifrado"
# La frase entra por un descriptor de archivo con printf, que es interno de bash, así que no aparece en la línea
# de comandos de ningún proceso ni en un archivo temporal. --no-symkey-cache evita que gpg-agent la guarde, y los
# parámetros de S2K fijan una derivación de clave lenta aunque no haya agente.
"$GPG" --batch --yes --quiet --pinentry-mode loopback --passphrase-fd 3 --no-symkey-cache \
    --s2k-mode 3 --s2k-digest-algo SHA512 --s2k-count 65011712 \
    --symmetric --cipher-algo AES256 --output "$BASE.dump.gpg" "$TMP/respaldo.dump" \
    3< <(printf '%s\n' "$RESPALDO_CLAVE")

if command -v sha256sum >/dev/null 2>&1; then
    (cd "$SALIDA" && sha256sum "$(basename "$BASE.dump.gpg")" > "$(basename "$BASE.dump.gpg").sha256")
else
    (cd "$SALIDA" && shasum -a 256 "$(basename "$BASE.dump.gpg")" > "$(basename "$BASE.dump.gpg").sha256")
fi
echo "ok respaldo cifrado en $BASE.dump.gpg"
