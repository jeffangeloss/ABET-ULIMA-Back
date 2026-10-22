#!/usr/bin/env bash
# Corre las pruebas de la entrega 1 sin Flyway, sobre bases desechables.
#   1. Regenera V1_03 desde la referencia y la compara con la versión guardada (salida determinista).
#   2. Crea dos bases nuevas, crea el esquema abet (lo que Flyway hace con createSchemas = true),
#      aplica las V en orden de versión, cada una en su transacción, y luego las R en orden alfabético.
#   3. Compara pg_dump --schema-only de las dos bases; deben ser idénticos.
#   4. Carga los datos sintéticos en la primera base y corre pruebas/pruebas.sql.
#   5. Borra las dos bases al terminar, pase lo que pase.
#
# Conexión por variables de entorno (las mismas de libpq), para correr igual en la Mac y en CI:
#   PGHOST, PGPORT, PGUSER y, si hace falta, PGPASSWORD (nunca se escribe en este archivo).
# Otras variables opcionales:
#   PSQL, PG_DUMP     rutas de psql y pg_dump (por defecto, los del PATH)
#   PYTHON            intérprete para el generador (por defecto python3)
#   PREFIJO_BD        prefijo de las bases desechables (por defecto abet_prueba)
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PSQL="${PSQL:-psql}"
PG_DUMP="${PG_DUMP:-pg_dump}"
PYTHON="${PYTHON:-python3}"
PREFIJO_BD="${PREFIJO_BD:-abet_prueba}"
export PGHOST="${PGHOST:-localhost}" PGPORT="${PGPORT:-5432}" PGUSER="${PGUSER:-postgres}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}" PGCLIENTENCODING=UTF8

BD_A="${PREFIJO_BD}_a_$$"
BD_B="${PREFIJO_BD}_b_$$"
TMP="$(mktemp -d)"

limpiar() {
    "$PSQL" -X -q -d postgres -c "DROP DATABASE IF EXISTS ${BD_A}" -c "DROP DATABASE IF EXISTS ${BD_B}" >/dev/null 2>&1 || true
    rm -rf "$TMP"
}
trap limpiar EXIT

paso() { printf '\n== %s\n' "$*"; }

paso "Generador de V1_03 determinista"
"$PYTHON" -I "$RAIZ/herramientas/generar_v1_03.py" "$RAIZ/referencia/ambiental_2026.json" "$TMP/V1_03.sql"
diff -u "$RAIZ/db/migration/V1_03__cargar_referencia_ambiental.sql" "$TMP/V1_03.sql"
echo "ok V1_03 regenerada es idéntica a la guardada"

# Versionadas en orden de versión (V1_01 < V1_02 < ... < V2_01) y repetibles en orden alfabético.
VERSIONADAS=$(cd "$RAIZ/db/migration" && ls V*__*.sql | sort -t_ -k1,1V -k2,2n)
REPETIBLES=$(cd "$RAIZ/db/migration" && ls R__*.sql 2>/dev/null | LC_ALL=C sort || true)

aplicar_migraciones() {
    local bd="$1"
    "$PSQL" -X -q -v ON_ERROR_STOP=1 -d postgres -c "CREATE DATABASE ${bd} TEMPLATE template0 ENCODING 'UTF8'"
    "$PSQL" -X -q -v ON_ERROR_STOP=1 -d "$bd" -c "CREATE SCHEMA abet"
    for f in $VERSIONADAS $REPETIBLES; do
        PGOPTIONS="-c client_min_messages=warning" \
            "$PSQL" -X -q -1 -v ON_ERROR_STOP=1 -d "$bd" -f "$RAIZ/db/migration/$f" >/dev/null
        echo "ok $bd  $f"
    done
}

paso "Migraciones en la base ${BD_A}"
aplicar_migraciones "$BD_A"
paso "Migraciones en la base ${BD_B}"
aplicar_migraciones "$BD_B"

paso "Comparación de pg_dump --schema-only"
# pg_dump 16.10 o posterior escribe \restrict y \unrestrict con una clave aleatoria en cada corrida; se quitan.
volcar() { "$PG_DUMP" --schema-only --no-owner --no-privileges -d "$1" | grep -vE '^\\(un)?restrict ' ; }
volcar "$BD_A" > "$TMP/a.sql"
volcar "$BD_B" > "$TMP/b.sql"
diff -u "$TMP/a.sql" "$TMP/b.sql"
echo "ok esquemas idénticos ($(wc -l < "$TMP/a.sql" | tr -d ' ') líneas de pg_dump)"

paso "Datos sintéticos"
"$PSQL" -X -q -1 -v ON_ERROR_STOP=1 -d "$BD_A" -f "$RAIZ/pruebas/datos_sinteticos.sql" >/dev/null
echo "ok datos sintéticos cargados"

paso "Aserciones (pruebas/pruebas.sql)"
"$PSQL" -X -q -v ON_ERROR_STOP=1 -d "$BD_A" -f "$RAIZ/pruebas/pruebas.sql" 2>&1 | sed -e 's/^psql:[^ ]* NOTICE:  /  /'
echo
echo "RESULTADO: todo pasó"
