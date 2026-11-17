#!/usr/bin/env bash
# Demo del corte 1 en la Mac, sin Neon, con el comando python -m abet_carga (parte de T039).
#
# Uso.
#   bash scripts/demo_corte1.sh [--conservar] [carpeta_de_salida]
#
# El guion arma con db/pruebas/cluster_desechable.sh un clúster de PostgreSQL 18 desechable, con su
# socket propio y sin TCP, así que nunca toca el clúster de la Mac ni abet_sis_med_dev. En ese
# clúster crea la base abet_demo_corte1_<pid> con V1_01 a la última migración versionada y las R__,
# en el orden de db/pruebas/correr_pruebas.sh, el rol de la aplicación abet_demo_app_corte1_<pid>
# de db/plataforma/neon/crear_rol_app.sql, la guardia de datos inventados,
# periodo_2026_2_inventado.sql y, si existe, varias_secciones_2026_2_inventado.sql.
#
# Después, con SET ROLE al rol de la aplicación, docente410@example.invalid carga
# export_inventado_410_con_error.xlsx en la 410 de 450002 en 2026-2, lo carga otra vez para mostrar
# que no se duplica y genera el R-17 y la constancia en la carpeta de salida. Con los datos de
# varias secciones, docente.varias@example.invalid ve dos exports rechazados por la sección y por la
# asignatura, publica cada export en su sección y queda detenido en la 410 de 450002, que no dicta.
# Los rechazos van antes que las publicaciones, porque una sección con carga publicada o un archivo
# ya publicado responden 409 antes de cotejar la sección (BR-CARGA-03).
#
# Al terminar apaga y borra el clúster, salvo con --conservar, que lo deja arriba y dice cómo
# conectarse y cómo apagarlo. Sale con 0 solo si la carga de la 410 da 11 leídas, 10 aceptadas y 1
# rechazada, si el R-17 trae 60,0 / 60,0 / 70,0 y si cada paso de varias secciones da lo esperado.

set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SALIDA="${TMPDIR:-/tmp}/abet_demo_corte1"
CONSERVAR=0
for argumento in "$@"; do
    case "$argumento" in
        --conservar) CONSERVAR=1 ;;
        -*) echo "Opción desconocida $argumento. Uso: bash scripts/demo_corte1.sh [--conservar] [carpeta]" >&2; exit 2 ;;
        *) SALIDA="$argumento" ;;
    esac
done

DATOS="$RAIZ/tests/datos_inventados"
VARIAS_SQL="$RAIZ/db/datos/varias_secciones_2026_2_inventado.sql"
BD="abet_demo_corte1_$$"
ROL="abet_demo_app_corte1_$$"
FALLAS=0

source "$RAIZ/db/pruebas/cluster_desechable.sh"
iniciar_cluster_desechable
if [ -z "${ABET_CLUSTER_DESECHABLE:-}" ]; then
    echo "La demo corre solo en un clúster desechable de la Mac; nada se crea." >&2
    exit 2
fi

terminar() {
    if [ "$CONSERVAR" -eq 1 ]; then
        printf '\nEl clúster sigue arriba en %s.\n' "$CLUSTER_CARPETA"
        printf 'Conexión  psql "host=%s port=%s dbname=%s user=postgres"\n' "$PGHOST" "$PGPORT" "$BD"
        printf 'Apagado   pg_ctl -D "%s/datos" -m fast stop && rm -rf "%s"\n' "$CLUSTER_CARPETA" "$CLUSTER_CARPETA"
    else
        detener_cluster_desechable
    fi
}
trap terminar EXIT

export PGCLIENTENCODING=UTF8
paso() { printf '\n== %s\n' "$*"; }
psql_bd() { psql -X -q -v ON_ERROR_STOP=1 -d "$BD" "$@"; }
falla() { echo "FALLA $*"; FALLAS=$((FALLAS + 1)); }
espera() {
    # espera "<descripción>" "<línea exacta>" "<salida>"
    if grep -qxF -- "$2" <<<"$3"; then echo "ok $1"; else falla "$1 (falta «$2»)"; fi
}

paso "Base $BD en el clúster desechable"
psql -X -q -v ON_ERROR_STOP=1 -d postgres -c "CREATE DATABASE $BD TEMPLATE template0 ENCODING 'UTF8'"
psql_bd -c "CREATE SCHEMA abet" -c "CREATE SCHEMA acceso"
VERSIONADAS=$(cd "$RAIZ/db/migration" && ls V*__*.sql | sort -t_ -k1,1V -k2,2n)
REPETIBLES=$(cd "$RAIZ/db/migration" && ls R__*.sql | LC_ALL=C sort)
for migracion in $VERSIONADAS $REPETIBLES; do
    PGOPTIONS="-c client_min_messages=warning" psql_bd -1 -f "$RAIZ/db/migration/$migracion" >/dev/null
    echo "ok $migracion"
done
env -u APP_DB_CLAVE psql -X -q -v ON_ERROR_STOP=1 -v rol_app="$ROL" -d "$BD" \
    -f "$RAIZ/db/plataforma/neon/crear_rol_app.sql" >/dev/null
echo "ok rol de la aplicación $ROL, sin contraseña"
for script in "$RAIZ/db/plataforma/neon/guardia_datos_inventados.sql" "$RAIZ/db/datos/periodo_2026_2_inventado.sql"; do
    psql_bd -f "$script" >/dev/null
    echo "ok ${script#"$RAIZ/"}"
done
VARIAS=0
if [ -f "$VARIAS_SQL" ]; then
    psql_bd -f "$VARIAS_SQL" >/dev/null
    VARIAS=1
    echo "ok ${VARIAS_SQL#"$RAIZ/"}"
fi

CONEXION="host=$PGHOST port=$PGPORT dbname=$BD user=postgres"
comando() {
    (cd "$RAIZ" && CONJUNTO_REGLAS=R-2026-BORRADOR GUARDIA_DATOS_INVENTADOS=1 \
        uv run --frozen python -m abet_carga "$@" --base "$CONEXION" --rol "$ROL")
}
cargar_en() {
    # cargar_en <export> <asignatura> <sección> <correo>; deja la salida en SALIDA_CMD y el código en CODIGO
    CODIGO=0
    SALIDA_CMD="$(comando cargar "$DATOS/$1" --asignatura "$2" --seccion "$3" --periodo 2026-2 --correo "$4")" \
        || CODIGO=$?
    printf '%s\n(salida %s)\n' "$SALIDA_CMD" "$CODIGO"
}
carga_de() { sed -n 's/^Carga: //p' <<<"$1"; }

paso "Primera carga del export de la 410 de 450002 como docente410@example.invalid"
cargar_en export_inventado_410_con_error.xlsx 450002 410 docente410@example.invalid
CARGA="$(carga_de "$SALIDA_CMD")"
espera "carga publicada" "Estado: PUBLICADA" "$SALIDA_CMD"
espera "11 leídas" "Filas leídas: 11" "$SALIDA_CMD"
espera "10 aceptadas" "Filas aceptadas: 10" "$SALIDA_CMD"
espera "1 rechazada" "Filas rechazadas: 1" "$SALIDA_CMD"
espera "rechazo de la fila 3" "Rechazo: fila 3, PI 5.2, NIVEL_FUERA_DE_ESCALA" "$SALIDA_CMD"

paso "Segunda carga del mismo export, que no se duplica"
cargar_en export_inventado_410_con_error.xlsx 450002 410 docente410@example.invalid
espera "la segunda carga devuelve la misma" "Resultado: YA_PUBLICADA (200)" "$SALIDA_CMD"
espera "mismo carga_id" "Carga: $CARGA" "$SALIDA_CMD"
CARGAS="$(psql_bd -At -c "SELECT count(*) FROM abet.carga")"
[ "$CARGAS" = 1 ] && echo "ok abet.carga tiene 1 fila" || falla "abet.carga tiene $CARGAS filas"

paso "R-17 y constancia de la carga $CARGA en $SALIDA"
CODIGO=0
SALIDA_CMD="$(comando r17 --carga "$CARGA" --carpeta "$SALIDA" --correo docente410@example.invalid)" || CODIGO=$?
printf '%s\n(salida %s)\n' "$SALIDA_CMD" "$CODIGO"
espera "cifras del R-17 según el comando" "Logro sobre calificados: 5.1 60,0 %, 5.2 60,0 %, 5.3 70,0 %" "$SALIDA_CMD"
R17="$(sed -n 's/^R-17: //p' <<<"$SALIDA_CMD")"
CIFRAS="$(cd "$RAIZ" && uv run --frozen python -I -c '
import sys, openpyxl
libro = openpyxl.load_workbook(sys.argv[1], read_only=True)
hoja = libro["Cursos de Carrera"]
print(" / ".join(f"{hoja.cell(row=fila, column=5).value * 100:.1f}".replace(".", ",") for fila in (24, 25, 26)))
libro.close()' "$R17" 2>&1 || true)"
[ "$CIFRAS" = "60,0 / 60,0 / 70,0" ] && echo "ok el R-17 releído trae $CIFRAS" || falla "el R-17 releído trae «$CIFRAS»"

paso "Consultas de control Q01 a Q14"
CONTROLES="$(psql -X -q -d "$BD" -f "$RAIZ/db/plataforma/neon/controles_neon.sql" 2>&1 || true)"
espera "Q01 a Q14 en cero" "RESULTADO: Q01 a Q14 devuelven 0 filas." "$CONTROLES"

if [ "$VARIAS" -eq 1 ]; then
    V=docente.varias@example.invalid
    paso "Varias secciones. El export de la 410 de 450010 subido en la 412 de 450010"
    cargar_en sintetico_20262_450010_410.xlsx 450010 412 "$V"
    espera "rechazada por la sección" \
        "Mensaje: El archivo corresponde a la sección 410 y usted eligió la 412. No se publicó." "$SALIDA_CMD"
    paso "Varias secciones. El export de la 412 de 450010 subido en la 412 de 450002"
    cargar_en sintetico_20262_450010_412.xlsx 450002 412 "$V"
    espera "rechazada por la asignatura" \
        "Mensaje: El archivo corresponde a la asignatura 450010 y usted eligió la 450002. No se publicó." "$SALIDA_CMD"
    for destino in "450002 412" "450010 410" "450010 412"; do
        set -- $destino
        paso "Varias secciones. sintetico_20262_$1_$2.xlsx en la $2 de $1"
        cargar_en "sintetico_20262_$1_$2.xlsx" "$1" "$2" "$V"
        espera "publicada en la $2 de $1" "Estado: PUBLICADA" "$SALIDA_CMD"
        espera "11 aceptadas en la $2 de $1" "Filas aceptadas: 11" "$SALIDA_CMD"
    done
    paso "Varias secciones. Intento en la 410 de 450002, que no dicta"
    cargar_en sintetico_20262_450002_412.xlsx 450002 410 "$V"
    espera "detenido por el alcance" "La sección no está a su cargo." "$SALIDA_CMD"
    [ "$CODIGO" -ne 0 ] && echo "ok sale con $CODIGO" || falla "el intento ajeno sale con 0"
else
    paso "Sin db/datos/varias_secciones_2026_2_inventado.sql, la demo omite las varias secciones"
fi

paso "Resultado"
if [ "$FALLAS" -eq 0 ]; then
    echo "Demo del corte 1 sin fallas. R-17 en $R17"
else
    echo "Demo del corte 1 con $FALLAS fallas."
    exit 1
fi
