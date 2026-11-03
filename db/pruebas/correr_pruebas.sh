#!/usr/bin/env bash
# Corre las pruebas de la base sin Flyway, sobre bases desechables.
#   1. Regenera V1_03 desde la referencia y la compara con la versión guardada (salida determinista).
#   2. Crea dos bases nuevas, crea los esquemas abet y acceso (lo que Flyway hace con createSchemas = true en una
#      base vacía), aplica las V en orden de versión, cada una en su transacción, y luego las R en orden alfabético.
#   3. Compara pg_dump --schema-only de las dos bases; deben ser idénticos. En la segunda base, el script de datos
#      de 2026-2 debe detenerse y deshacer todo cuando un usuario de prueba ya existe con otro rol. El script de
#      varias secciones debe detenerse antes de los datos de 2026-2, sin la asignación de la 410 de 450010 (en una
#      copia del archivo), con la 412 de 450010 ya registrada sin curso de Blackboard, con una asignación de más y
#      con un segundo profesor de prueba en la 410 de 450010, y después pasa dos veces sin duplicar.
#   4. Carga en la primera base los datos sintéticos, dos veces los datos de 2026-2 y dos veces los de varias
#      secciones, y corre pruebas/pruebas.sql.
#   5. Ensaya en una tercera base el camino de Neon (T021 y T027). Aplica V1_01 a V1_08 y las R y carga los datos
#      sintéticos. Antes de V1_09, crear_rol_app.sql debe rechazar abet_respaldo y fallar sin dejar el rol de prueba.
#      Aplica después las V que siguen, con V1_09 creando acceso, compara su esquema con el de la segunda base y
#      corre los scripts de plataforma y de datos en el orden de T027, las consultas de control y
#      pruebas/probar_rol_app.sql con un rol de prueba de nombre único. Al final vuelve a aplicar las R, que quitan
#      al rol el SELECT de las vistas hasta que crear_rol_app.sql corre otra vez, y corre las consultas de control
#      sin -v ON_ERROR_STOP=1, como el paso 5 de T027, con una carga REEMPLAZADA sin reemplazo, que deben terminar
#      con la salida 3. El script de varias secciones no entra en T027, así que esta base no lo recibe.
#   6. Prueba la guardia de datos inventados en una cuarta base con pruebas/probar_guardia.sql.
#   7. Borra las bases y el rol de prueba al terminar, pase lo que pase, y apaga el clúster desechable.
#
# Conexión. En la Mac, el script arranca su propio clúster desechable (pruebas/cluster_desechable.sh), que vive lo
# que dura la corrida, e ignora PGHOST y PGPORT, así que nunca toca el clúster de localhost:5432. En la CI
# (GITHUB_ACTIONS=true) usa las variables de libpq del job, PGHOST, PGPORT, PGUSER y, si hace falta, PGPASSWORD
# (nunca se escribe en este archivo), con un PGUSER que puede crear bases y roles, como postgres.
# Otras variables opcionales:
#   PSQL, PG_DUMP     rutas de psql y pg_dump (por defecto, los del PATH; psql 15 o posterior por \getenv)
#   PYTHON            intérprete para el generador (por defecto python3)
#   PREFIJO_BD        prefijo de las bases y del rol desechables (por defecto abet_prueba)
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=cluster_desechable.sh
source "$RAIZ/pruebas/cluster_desechable.sh"
iniciar_cluster_desechable
trap detener_cluster_desechable EXIT
PSQL="${PSQL:-psql}"
PG_DUMP="${PG_DUMP:-pg_dump}"
PYTHON="${PYTHON:-python3}"
PREFIJO_BD="${PREFIJO_BD:-abet_prueba}"
export PGHOST="${PGHOST:-localhost}" PGPORT="${PGPORT:-5432}" PGUSER="${PGUSER:-postgres}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}" PGCLIENTENCODING=UTF8

BD_A="${PREFIJO_BD}_a_$$"
BD_B="${PREFIJO_BD}_b_$$"
BD_N="${PREFIJO_BD}_neon_$$"
BD_G="${PREFIJO_BD}_guardia_$$"
# Los roles son del clúster y no de una base, así que el de prueba lleva el número del proceso en su nombre.
ROL_APP="${PREFIJO_BD}_app_$$"
# Dueño de la base de la guardia sin superusuario, como el dueño de la base en Neon, para la marca de T077.
DUENO="${PREFIJO_BD}_dueno_$$"
TMP="$(mktemp -d)"

limpiar() {
    # Primero las bases, que guardan los permisos del rol; después el rol. FORCE cierra una conexión que quede abierta.
    "$PSQL" -X -q -d postgres -c "DROP DATABASE IF EXISTS ${BD_A} WITH (FORCE)" \
        -c "DROP DATABASE IF EXISTS ${BD_B} WITH (FORCE)" -c "DROP DATABASE IF EXISTS ${BD_N} WITH (FORCE)" \
        -c "DROP DATABASE IF EXISTS ${BD_G} WITH (FORCE)" >/dev/null 2>&1 || true
    if ! "$PSQL" -X -q -v ON_ERROR_STOP=1 -d postgres -c "DROP ROLE IF EXISTS ${ROL_APP}" >/dev/null 2>&1; then
        echo "Aviso: no se pudo borrar el rol de prueba ${ROL_APP}; hay que borrarlo a mano con DROP ROLE." >&2
    fi
    "$PSQL" -X -q -d postgres -c "DROP ROLE IF EXISTS ${DUENO}" >/dev/null 2>&1 || true
    rm -rf "$TMP"
    detener_cluster_desechable
}
trap limpiar EXIT

paso() { printf '\n== %s\n' "$*"; }
# Muestra los NOTICE de psql sin su prefijo, como en las aserciones de pruebas.sql.
sin_prefijo() { sed -e 's/^psql:[^ ]* NOTICE:  /  /'; }
# Valor de una consulta, sin encabezado ni alineación.
valor() { "$PSQL" -X -At -v ON_ERROR_STOP=1 -d "$1" -c "$2"; }

paso "Generador de V1_03 determinista"
"$PYTHON" -I "$RAIZ/herramientas/generar_v1_03.py" "$RAIZ/referencia/ambiental_2026.json" "$TMP/V1_03.sql"
diff -u "$RAIZ/migration/V1_03__cargar_referencia_ambiental.sql" "$TMP/V1_03.sql"
echo "ok V1_03 regenerada es idéntica a la guardada"

# Versionadas en orden de versión (V1_01 < V1_02 < ... < V2_01) y repetibles en orden alfabético.
VERSIONADAS=$(cd "$RAIZ/migration" && ls V*__*.sql | sort -t_ -k1,1V -k2,2n)
REPETIBLES=$(cd "$RAIZ/migration" && ls R__*.sql 2>/dev/null | LC_ALL=C sort || true)
# V1_01 a V1_08 son las que T021 aplica en Neon desde ABET_ULIMA; las que siguen llegan con T027.
EN_NEON=$(cd "$RAIZ/migration" && ls V1_0[1-8]__*.sql | sort -t_ -k1,1V -k2,2n)
NUEVAS=$(printf '%s\n' $VERSIONADAS | grep -vxF "$(printf '%s\n' $EN_NEON)" || true)

crear_base() {
    local bd="$1"; shift
    "$PSQL" -X -q -v ON_ERROR_STOP=1 -d postgres -c "CREATE DATABASE ${bd} TEMPLATE template0 ENCODING 'UTF8'"
    for esquema in "$@"; do
        "$PSQL" -X -q -v ON_ERROR_STOP=1 -d "$bd" -c "CREATE SCHEMA ${esquema}"
    done
}

aplicar() {
    local bd="$1"; shift
    for f in "$@"; do
        PGOPTIONS="-c client_min_messages=warning" \
            "$PSQL" -X -q -1 -v ON_ERROR_STOP=1 -d "$bd" -f "$RAIZ/migration/$f" >/dev/null
        echo "ok $bd  $f"
    done
}

# Scripts de plataforma y de datos, sin -1 porque cada uno abre y cierra su propia transacción.
correr() {
    local bd="$1" archivo="$2"; shift 2
    "$PSQL" -X -q -v ON_ERROR_STOP=1 "$@" -d "$bd" -f "$RAIZ/$archivo" 2>&1 | sin_prefijo
}

# El rol de prueba nunca recibe contraseña, aunque la terminal tenga APP_DB_CLAVE para Neon.
crear_rol() { env -u APP_DB_CLAVE "$PSQL" -X -q -v ON_ERROR_STOP=1 -v rol_app="$ROL_APP" -d "$1" \
                  -f "$RAIZ/plataforma/neon/crear_rol_app.sql" 2>&1 | sin_prefijo; }

# Las consultas de control deben terminar en cero, con la línea de RESULTADO exacta de controles_neon.sql. Con una
# falla se muestra la salida completa.
controles() {
    local salida
    if ! salida="$("$PSQL" -X -q -d "$1" -f "$RAIZ/plataforma/neon/controles_neon.sql" 2>&1)" \
       || ! grep -qxF 'RESULTADO: Q01 a Q14 devuelven 0 filas.' <<<"$salida"; then
        printf '%s\n' "$salida"
        echo "FALLA controles_neon.sql en $1"
        return 1
    fi
    echo "ok controles_neon.sql en $1  Q01 a Q14 devuelven 0 filas."
}

# Un caso que debe fallar. Exige la salida 3 de psql, la de un error con ON_ERROR_STOP, y el texto esperado en la
# salida; si no, muestra la salida completa y detiene la prueba.
debe_fallar() {
    local descripcion="$1" texto="$2" salida codigo=0
    shift 2
    salida="$("$@" 2>&1)" || codigo=$?
    if [ "$codigo" -ne 3 ] || ! grep -qF -- "$texto" <<<"$salida"; then
        printf '%s\n' "$salida"
        echo "FALLA ${descripcion}: se esperaba la salida 3 con «${texto}» y psql terminó con ${codigo}"
        return 1
    fi
    echo "ok ${descripcion} (salida 3)"
}

# SELECT del rol de prueba sobre las dos vistas, como «true,true» o «false,false».
vistas_del_rol() {
    valor "$1" "SELECT CAST(has_table_privilege('${ROL_APP}', 'abet.v_r17_por_pi', 'SELECT') AS text) || ','
                || CAST(has_table_privilege('${ROL_APP}', 'abet.v_tabla_maestra_pi', 'SELECT') AS text)"
}

paso "Migraciones en la base ${BD_A}"
crear_base "$BD_A" abet acceso
aplicar "$BD_A" $VERSIONADAS $REPETIBLES
paso "Migraciones en la base ${BD_B}"
crear_base "$BD_B" abet acceso
aplicar "$BD_B" $VERSIONADAS $REPETIBLES

paso "Comparación de pg_dump --schema-only"
# pg_dump 16.10 o posterior escribe \restrict y \unrestrict con una clave aleatoria en cada corrida; se quitan.
volcar() { "$PG_DUMP" --schema-only --no-owner --no-privileges -d "$1" | grep -vE '^\\(un)?restrict ' ; }
volcar "$BD_A" > "$TMP/a.sql"
volcar "$BD_B" > "$TMP/b.sql"
diff -u "$TMP/a.sql" "$TMP/b.sql"
echo "ok esquemas idénticos ($(wc -l < "$TMP/a.sql" | tr -d ' ') líneas de pg_dump)"

paso "Script de datos con un usuario de prueba de otro rol en ${BD_B}, que debe detenerse y deshacer todo"
"$PSQL" -X -q -v ON_ERROR_STOP=1 -d "$BD_B" \
    -c "INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES ('docente410@example.invalid', 'COORDINADOR')"
debe_fallar "periodo_2026_2_inventado.sql con docente410 registrado como COORDINADOR" \
    "Los usuarios de prueba no tienen el rol o el estado esperados" \
    "$PSQL" -X -q -v ON_ERROR_STOP=1 -d "$BD_B" -f "$RAIZ/datos/periodo_2026_2_inventado.sql"
QUEDAN="$(valor "$BD_B" "SELECT (SELECT count(*) FROM abet.catalogo_vigencia) || '/' || (SELECT count(*) FROM abet.seccion)
                         || '/' || (SELECT count(*) FROM abet.plan_medicion) || '/' || (SELECT count(*) FROM acceso.docente_seccion)
                         || '/' || (SELECT string_agg(correo || '=' || rol, ',') FROM acceso.usuario_autorizado)")"
if [ "$QUEDAN" != "0/0/0/0/docente410@example.invalid=COORDINADOR" ]; then
    echo "FALLA el script de datos dejó filas aunque falló (vigencias/secciones/planes/asignaciones/usuarios = ${QUEDAN})"
    exit 1
fi
echo "ok el script de datos no deja vigencias, secciones, planes ni asignaciones, y el usuario sigue como estaba"

paso "Script de varias secciones en ${BD_B}, que debe detenerse y deshacer todo cuando algo no queda como dice su cabecera"
VARIAS="$RAIZ/datos/varias_secciones_2026_2_inventado.sql"
debe_fallar "varias_secciones_2026_2_inventado.sql antes de periodo_2026_2_inventado.sql" \
    "Faltan los datos de db/datos/periodo_2026_2_inventado.sql" \
    "$PSQL" -X -q -v ON_ERROR_STOP=1 -d "$BD_B" -f "$VARIAS"
QUEDAN="$(valor "$BD_B" "SELECT (SELECT count(*) FROM abet.catalogo_vigencia) || '/' || (SELECT count(*) FROM abet.seccion)
                         || '/' || (SELECT count(*) FROM abet.plan_medicion) || '/' || (SELECT count(*) FROM acceso.docente_seccion)
                         || '/' || (SELECT string_agg(correo || '=' || rol, ',') FROM acceso.usuario_autorizado)")"
if [ "$QUEDAN" != "0/0/0/0/docente410@example.invalid=COORDINADOR" ]; then
    echo "FALLA el script de varias secciones dejó filas aunque falló (vigencias/secciones/planes/asignaciones/usuarios = ${QUEDAN})"
    exit 1
fi
echo "ok el script de varias secciones no deja filas sin los datos de 2026-2"
# Con docente410 otra vez PROFESOR, los datos de 2026-2 pasan, y los casos que siguen parten de ellos.
"$PSQL" -X -q -v ON_ERROR_STOP=1 -d "$BD_B" \
    -c "UPDATE acceso.usuario_autorizado SET rol = 'PROFESOR' WHERE correo = 'docente410@example.invalid'"
correr "$BD_B" datos/periodo_2026_2_inventado.sql
# Copia del archivo sin la asignación de la 410 de 450010, una línea propia del VALUES de acceso.docente_seccion.
LINEA_ASIGNACION="             ('450010', '410'),"
grep -vxF -- "$LINEA_ASIGNACION" "$VARIAS" > "$TMP/varias_sin_asignacion.sql" || true
if [ "$(( $(wc -l < "$VARIAS") - $(wc -l < "$TMP/varias_sin_asignacion.sql") ))" -ne 1 ]; then
    echo "FALLA la copia sin la asignación de la 410 de 450010 debía quitar exactamente una línea de ${VARIAS}"
    exit 1
fi
debe_fallar "varias_secciones_2026_2_inventado.sql sin la asignación de la 410 de 450010" \
    "no dicta exactamente la 412 de 450002 y la 410 y la 412 de 450010 en 2026-2 (450002-412,450010-412)" \
    "$PSQL" -X -q -v ON_ERROR_STOP=1 -d "$BD_B" -f "$TMP/varias_sin_asignacion.sql"
QUEDAN="$(valor "$BD_B" "SELECT (SELECT count(*) FROM abet.plan_medicion pm JOIN abet.asignatura a
                                   ON a.asignatura_id = pm.asignatura_id AND a.codigo = '450010')
                         || '/' || (SELECT count(*) FROM abet.seccion s JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
                                     WHERE (a.codigo, s.numero) IN (('450002', '412'), ('450010', '410'), ('450010', '412')))
                         || '/' || (SELECT count(*) FROM acceso.usuario_autorizado WHERE correo = 'docente.varias@example.invalid')
                         || '/' || (SELECT count(*) FROM acceso.docente_seccion)")"
if [ "$QUEDAN" != "0/0/0/2" ]; then
    echo "FALLA el script de varias secciones dejó filas aunque falló (planes de 450010/secciones nuevas/usuario nuevo/asignaciones = ${QUEDAN})"
    exit 1
fi
echo "ok el script de varias secciones deshace todo, sin plan de 450010, secciones nuevas ni docente.varias@example.invalid"
# Los tres casos que siguen arman la condición en una transacción que no se confirma, así que la base queda igual.
debe_fallar "varias_secciones_2026_2_inventado.sql con la 412 de 450010 ya registrada sin curso de Blackboard" \
    "450010-412=sin curso" \
    "$PSQL" -X -q -v ON_ERROR_STOP=1 -d "$BD_B" -c "BEGIN" \
    -c "INSERT INTO abet.seccion (periodo_id, asignatura_id, numero)
        SELECT pe.periodo_id, a.asignatura_id, '412' FROM abet.periodo pe, abet.asignatura a
        WHERE pe.codigo = '2026-2' AND a.codigo = '450010'" \
    -f "$VARIAS"
debe_fallar "varias_secciones_2026_2_inventado.sql con docente.varias@example.invalid asignado también a la 410 de 450002" \
    "en 2026-2 (450002-410,450002-412,450010-410,450010-412)" \
    "$PSQL" -X -q -v ON_ERROR_STOP=1 -d "$BD_B" -c "BEGIN" \
    -c "INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES ('docente.varias@example.invalid', 'PROFESOR')" \
    -c "INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)
        SELECT u.usuario_id, s.seccion_id FROM acceso.usuario_autorizado u, abet.seccion s
        JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002'
        WHERE u.correo = 'docente.varias@example.invalid' AND s.numero = '410'" \
    -f "$VARIAS"
# docente.varias@example.invalid dicta exactamente sus tres secciones, así que solo el bloque que exige un único
# profesor de prueba por sección detiene este caso.
debe_fallar "varias_secciones_2026_2_inventado.sql con docente410@example.invalid asignado también a la 410 de 450010" \
    "no tienen solo su profesor de prueba (450002-410=docente410@example.invalid,450002-411=docente411@example.invalid,450002-412=docente.varias@example.invalid,450010-410=docente.varias@example.invalid,450010-410=docente410@example.invalid,450010-412=docente.varias@example.invalid)" \
    "$PSQL" -X -q -v ON_ERROR_STOP=1 -d "$BD_B" -c "BEGIN" \
    -c "INSERT INTO abet.seccion (periodo_id, asignatura_id, numero, curso_blackboard)
        SELECT pe.periodo_id, a.asignatura_id, '410', 'SINTETICO_20262_450010_410' FROM abet.periodo pe, abet.asignatura a
        WHERE pe.codigo = '2026-2' AND a.codigo = '450010'" \
    -c "INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)
        SELECT u.usuario_id, s.seccion_id FROM acceso.usuario_autorizado u, abet.seccion s
        JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450010'
        WHERE u.correo = 'docente410@example.invalid' AND s.numero = '410'" \
    -f "$VARIAS"
# En una base sin los datos sintéticos, dos corridas dejan cada fila una sola vez.
correr "$BD_B" datos/varias_secciones_2026_2_inventado.sql
correr "$BD_B" datos/varias_secciones_2026_2_inventado.sql
QUEDAN="$(valor "$BD_B" "SELECT (SELECT count(*) FROM abet.plan_medicion) || '/' || (SELECT count(*) FROM abet.seccion)
                         || '/' || (SELECT count(*) FROM acceso.usuario_autorizado) || '/' || (SELECT count(*) FROM acceso.docente_seccion)")"
if [ "$QUEDAN" != "6/5/4/5" ]; then
    echo "FALLA dos corridas de los scripts de datos debían dejar 6 planes, 5 secciones, 4 usuarios y 5 asignaciones (${QUEDAN})"
    exit 1
fi
echo "ok dos corridas del script de varias secciones dejan 6 filas de plan, 5 secciones, 4 usuarios y 5 asignaciones"
controles "$BD_B"

paso "Datos sintéticos, datos de 2026-2 (dos veces) y datos de varias secciones (dos veces) en ${BD_A}"
"$PSQL" -X -q -1 -v ON_ERROR_STOP=1 -d "$BD_A" -f "$RAIZ/pruebas/datos_sinteticos.sql" >/dev/null
echo "ok datos sintéticos cargados"
correr "$BD_A" datos/periodo_2026_2_inventado.sql
correr "$BD_A" datos/periodo_2026_2_inventado.sql
correr "$BD_A" datos/varias_secciones_2026_2_inventado.sql
correr "$BD_A" datos/varias_secciones_2026_2_inventado.sql

paso "Aserciones (pruebas/pruebas.sql)"
"$PSQL" -X -q -v ON_ERROR_STOP=1 -v controles_neon="$RAIZ/plataforma/neon/controles_neon.sql" -d "$BD_A" \
    -f "$RAIZ/pruebas/pruebas.sql" 2>&1 | sin_prefijo

paso "Ensayo de Neon en ${BD_N}, con V1_01 a V1_08, datos sintéticos y después V1_09 (T021 y T027)"
crear_base "$BD_N" abet
aplicar "$BD_N" $EN_NEON $REPETIBLES
"$PSQL" -X -q -1 -v ON_ERROR_STOP=1 -d "$BD_N" -f "$RAIZ/pruebas/datos_sinteticos.sql" >/dev/null
echo "ok datos sintéticos cargados antes de V1_09"
# Sin el esquema acceso, crear_rol_app.sql falla en su transacción, así que tampoco deja creado ningún rol.
debe_fallar "crear_rol_app.sql rechaza abet_respaldo como rol de la aplicación" \
    "El rol abet_respaldo no puede ser el rol de la aplicación" \
    env -u APP_DB_CLAVE "$PSQL" -X -q -v ON_ERROR_STOP=1 -v rol_app=abet_respaldo -d "$BD_N" \
    -f "$RAIZ/plataforma/neon/crear_rol_app.sql"
# VERBOSITY=sqlstate deja solo el código del error, 3F000 para un esquema que no existe, en cualquier idioma.
debe_fallar "crear_rol_app.sql antes de V1_09, sin el esquema acceso" "3F000" \
    env -u APP_DB_CLAVE "$PSQL" -X -q -v ON_ERROR_STOP=1 -v VERBOSITY=sqlstate -v rol_app="$ROL_APP" -d "$BD_N" \
    -f "$RAIZ/plataforma/neon/crear_rol_app.sql"
if [ "$(valor postgres "SELECT count(*) FROM pg_roles WHERE rolname = '${ROL_APP}'")" != 0 ]; then
    echo "FALLA crear_rol_app.sql dejó el rol ${ROL_APP} aunque falló"
    exit 1
fi
echo "ok crear_rol_app.sql deshace todo al fallar y no deja el rol ${ROL_APP}"
aplicar "$BD_N" $NUEVAS
volcar "$BD_N" > "$TMP/n.sql"
diff -u "$TMP/b.sql" "$TMP/n.sql"
echo "ok V1_09 sobre una base con datos deja el mismo esquema que una base nueva"
controles "$BD_N"

paso "Scripts de plataforma y de datos en ${BD_N}, en el orden de T027"
crear_rol "$BD_N"
# Un permiso de más, puesto a mano, desaparece al repetir el script, que deja el rol como lo declara el archivo.
"$PSQL" -X -q -v ON_ERROR_STOP=1 -d "$BD_N" -c "GRANT DELETE ON abet.medicion TO ${ROL_APP}"
crear_rol "$BD_N"
correr "$BD_N" plataforma/neon/guardia_datos_inventados.sql
correr "$BD_N" datos/periodo_2026_2_inventado.sql
correr "$BD_N" datos/periodo_2026_2_inventado.sql
controles "$BD_N"

paso "Rol de la aplicación (pruebas/probar_rol_app.sql)"
correr "$BD_N" pruebas/probar_rol_app.sql -v rol_app="$ROL_APP"
controles "$BD_N"

paso "Repetibles otra vez en ${BD_N}, como un migrate que cambia una R__"
aplicar "$BD_N" $REPETIBLES
if [ "$(vistas_del_rol "$BD_N")" != "false,false" ]; then
    echo "FALLA las R reaplicadas debían quitar al rol el SELECT de v_r17_por_pi y de v_tabla_maestra_pi"
    exit 1
fi
echo "ok las R reaplicadas dejan al rol sin el SELECT de v_r17_por_pi ni de v_tabla_maestra_pi"
crear_rol "$BD_N"
if [ "$(vistas_del_rol "$BD_N")" != "true,true" ]; then
    echo "FALLA crear_rol_app.sql debía reponer el SELECT de las dos vistas"
    exit 1
fi
echo "ok crear_rol_app.sql, corrido otra vez, repone el SELECT de las dos vistas"

paso "Consultas de control con una carga REEMPLAZADA sin reemplazo en ${BD_N}, en una transacción que no se confirma"
# Sin -v ON_ERROR_STOP=1, como el paso 5 del orden de T027 en db/README.md, así la salida 3 depende del
# \set ON_ERROR_STOP 1 de controles_neon.sql. Si el UPDATE falla, la transacción queda abortada, el archivo se detiene
# en su primera sentencia sin la línea de RESULTADO esperada y debe_fallar detiene igual la prueba.
debe_fallar "controles_neon.sql con la carga de la 410 en REEMPLAZADA sin reemplazo (Q14)" \
    "RESULTADO: al menos una consulta de control devuelve filas" \
    "$PSQL" -X -q -d "$BD_N" -c "BEGIN" \
    -c "UPDATE abet.carga c SET estado = 'REEMPLAZADA' FROM abet.seccion s
        WHERE s.seccion_id = c.seccion_id AND s.numero = '410' AND c.estado = 'PUBLICADA'" \
    -f "$RAIZ/plataforma/neon/controles_neon.sql"
controles "$BD_N"

paso "Guardia de datos inventados en ${BD_G}"
crear_base "$BD_G" abet acceso
aplicar "$BD_G" $VERSIONADAS $REPETIBLES
crear_rol "$BD_G"
correr "$BD_G" plataforma/neon/guardia_datos_inventados.sql
correr "$BD_G" plataforma/neon/guardia_datos_inventados.sql
correr "$BD_G" datos/periodo_2026_2_inventado.sql
correr "$BD_G" datos/periodo_2026_2_inventado.sql
correr "$BD_G" pruebas/probar_guardia.sql -v rol_app="$ROL_APP"
controles "$BD_G"

paso "Marca de entorno de Vercel en ${BD_G}, con un dueño sin superusuario como en Neon (T077)"
"$PSQL" -X -q -v ON_ERROR_STOP=1 -d postgres -c "CREATE ROLE ${DUENO} NOLOGIN" \
    -c "ALTER DATABASE ${BD_G} OWNER TO ${DUENO}"
# SET ROLE corre el script con los permisos del dueño, igual que probar_rol_app.sql con los del rol de la aplicación.
marcar() { "$PSQL" -X -q -v ON_ERROR_STOP=1 "$@" -d "$BD_G" -c "SET ROLE ${DUENO}" \
               -f "$RAIZ/plataforma/neon/marcar_entorno.sql" 2>&1 | sin_prefijo; }
# La API lee la marca con el rol de la aplicación, que no es dueño de la base.
marca() { "$PSQL" -X -q -At -v ON_ERROR_STOP=1 -d "$BD_G" -c "SET ROLE ${ROL_APP}" \
              -c "SELECT coalesce(shobj_description(oid, 'pg_database'), '') FROM pg_database WHERE datname = current_database()"; }
marcar -v entorno=preview
if [ "$(marca)" != abet.entorno=preview ]; then
    echo "FALLA marcar_entorno.sql debía dejar el comentario abet.entorno=preview ($(marca))"
    exit 1
fi
echo "ok el dueño sin superusuario marca la base con preview, y el rol de la aplicación lee la marca"
marcar -v entorno=production
if [ "$(marca)" != abet.entorno=production ]; then
    echo "FALLA una segunda corrida de marcar_entorno.sql debía cambiar la marca a production ($(marca))"
    exit 1
fi
echo "ok una segunda corrida de marcar_entorno.sql cambia la marca a production"
debe_fallar "marcar_entorno.sql rechaza un entorno que no es production ni preview" "production o preview" \
    "$PSQL" -X -q -v ON_ERROR_STOP=1 -v entorno=development -d "$BD_G" -c "SET ROLE ${DUENO}" \
    -f "$RAIZ/plataforma/neon/marcar_entorno.sql"
# VERBOSITY=sqlstate deja solo el código del error, 42601 para el :'entorno' que psql no reemplaza.
debe_fallar "marcar_entorno.sql sin -v entorno" "42601" \
    "$PSQL" -X -q -v ON_ERROR_STOP=1 -v VERBOSITY=sqlstate -d "$BD_G" -c "SET ROLE ${DUENO}" \
    -f "$RAIZ/plataforma/neon/marcar_entorno.sql"
# 42501 es insufficient_privilege. El archivo de -f hace que psql termine con la salida 3, como el resto de los casos.
debe_fallar "el rol de la aplicación no cambia la marca" "42501" \
    "$PSQL" -X -q -v ON_ERROR_STOP=1 -v VERBOSITY=sqlstate -d "$BD_G" -c "SET ROLE ${ROL_APP}" \
    -f <(printf "COMMENT ON DATABASE %s IS 'abet.entorno=preview';\n" "$BD_G")
if [ "$(marca)" != abet.entorno=production ]; then
    echo "FALLA un intento rechazado cambió la marca ($(marca))"
    exit 1
fi
echo "ok los intentos rechazados no cambian la marca"

echo
echo "RESULTADO: todo pasó"
