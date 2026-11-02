# Clúster de PostgreSQL 16 desechable para los guiones que crean o borran bases. Se carga con
#   source db/pruebas/cluster_desechable.sh
#   iniciar_cluster_desechable
# y el guion llama a detener_cluster_desechable al salir, pase lo que pase.
#
# Fuera de la integración continua (continuous integration, CI), las pruebas nunca usan el clúster de la Mac
# (localhost:5432), donde viven abet_sis_med_dev y las bases de otros proyectos. El 2026-10-28 una prueba borró
# abet_sis_med_dev, y desde entonces las bases desechables viven en un clúster que también es desechable.
# iniciar_cluster_desechable corre initdb en una carpeta temporal y pg_ctl arranca el servidor escuchando solo en un
# socket de Unix de esa carpeta, sin TCP, y deja PGHOST, PGPORT y PGUSER apuntando a ese clúster. Después comprueba
# con SHOW data_directory que el servidor que responde es ese clúster. En la CI no hace nada, porque el
# servicio postgres:16 del job ya es desechable. La CI exige GITHUB_ACTIONS=true, RUNNER_TEMP no vacío y un sistema distinto de
# Darwin, así que exportar solo GITHUB_ACTIONS=true en la Mac no abre el clúster local. tests/cluster_desechable.py hace lo mismo para pytest.

CLUSTER_PUERTO=54329

iniciar_cluster_desechable() {
    if [ "${GITHUB_ACTIONS:-}" = "true" ] && [ -n "${RUNNER_TEMP:-}" ] && [ "$(uname -s)" != "Darwin" ]; then
        return 0
    fi
    # Un socket de Unix admite rutas de hasta 103 bytes en macOS, así que una carpeta temporal larga cede a /tmp.
    local base="${TMPDIR:-/tmp}"
    base="${base%/}"
    if [ "${#base}" -gt 60 ]; then
        base=/tmp
    fi
    CLUSTER_CARPETA="$(mktemp -d "$base/abet_pg_XXXXXX")"
    if ! LC_ALL=en_US.UTF-8 initdb -D "$CLUSTER_CARPETA/datos" -U postgres -A trust -E UTF8 --locale=en_US.UTF-8 \
            >"$CLUSTER_CARPETA/initdb.log" 2>&1; then
        echo "initdb no pudo crear el clúster desechable:" >&2
        cat "$CLUSTER_CARPETA/initdb.log" >&2
        rm -rf "$CLUSTER_CARPETA"
        return 1
    fi
    if ! LC_ALL=en_US.UTF-8 pg_ctl -D "$CLUSTER_CARPETA/datos" -l "$CLUSTER_CARPETA/servidor.log" -w \
            -o "-p $CLUSTER_PUERTO -k $CLUSTER_CARPETA -c listen_addresses='' -c fsync=off -c full_page_writes=off -c synchronous_commit=off" \
            start >/dev/null; then
        echo "pg_ctl no pudo arrancar el clúster desechable:" >&2
        cat "$CLUSTER_CARPETA/servidor.log" >&2
        rm -rf "$CLUSTER_CARPETA"
        return 1
    fi
    export PGHOST="$CLUSTER_CARPETA" PGPORT="$CLUSTER_PUERTO" PGUSER=postgres
    export ABET_CLUSTER_DESECHABLE="$CLUSTER_CARPETA/datos"
    local respuesta
    respuesta="$(psql -X -At -d postgres -c 'SHOW data_directory')"
    if [ "$(cd "$respuesta" && pwd -P)" != "$(cd "$ABET_CLUSTER_DESECHABLE" && pwd -P)" ]; then
        echo "El servidor de PGHOST=$PGHOST no es el clúster desechable; nada se crea ni se borra." >&2
        detener_cluster_desechable
        return 1
    fi
}

detener_cluster_desechable() {
    if [ -n "${CLUSTER_CARPETA:-}" ] && [ -d "$CLUSTER_CARPETA" ]; then
        pg_ctl -D "$CLUSTER_CARPETA/datos" -m immediate -w stop >/dev/null 2>&1 || true
        rm -rf "$CLUSTER_CARPETA"
    fi
}
