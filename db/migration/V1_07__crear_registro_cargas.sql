-- V1_07  Registro de archivos, cargas, columnas reconocidas y rechazos (solo DDL).
-- Cubre C9 (huella SHA-256 única), C1 (filas leídas = filas del archivo = aceptadas + rechazadas; cero filas
-- no se publica), H09 (el export de Blackboard es la entrada; el R-17 histórico queda marcado como otra fuente),
-- H57 (reemplazo versionado de una carga publicada), H66 (solo se registran columnas de PI), C3 y C5 (rechazo
-- por fila con motivo), H01 (puntaje máximo declarado), H02 (las reglas de la carga son de la carrera dueña
-- de sus PI) y C6 (el encabezado empieza por el código exacto del PI, así «6.10» no entra como 6.1).
-- Nada de esta migración guarda nombres ni valores leídos del archivo.

CREATE TABLE abet.archivo_origen (
    archivo_id      integer      GENERATED ALWAYS AS IDENTITY,
    sha256          char(64)     NOT NULL,
    nombre_archivo  varchar(255) NOT NULL,
    hoja            varchar(100) NULL,
    filas_de_datos  integer      NOT NULL,
    tipo_fuente     varchar(17)  NOT NULL DEFAULT 'BLACKBOARD_EXPORT',
    recibido_en     timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT pk_archivo_origen         PRIMARY KEY (archivo_id),
    CONSTRAINT uq_archivo_origen_sha256  UNIQUE (sha256),
    -- Clave extendida para que la carga copie las filas de datos del archivo con una FK compuesta.
    CONSTRAINT uq_archivo_origen_filas   UNIQUE (archivo_id, filas_de_datos),
    CONSTRAINT ck_archivo_origen_tipo    CHECK (tipo_fuente IN ('BLACKBOARD_EXPORT', 'R17_HISTORICO')),
    CONSTRAINT ck_archivo_origen_sha256  CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_archivo_origen_nombre  CHECK (nombre_archivo !~ '[/\\]'),
    CONSTRAINT ck_archivo_origen_filas   CHECK (filas_de_datos >= 0)
);
COMMENT ON TABLE abet.archivo_origen IS 'Export de Blackboard recibido; la huella impide registrar dos veces el mismo archivo (C9).';
COMMENT ON COLUMN abet.archivo_origen.nombre_archivo IS 'Solo el nombre, sin la ruta local de quien carga.';
COMMENT ON COLUMN abet.archivo_origen.filas_de_datos IS 'Filas de datos medidas en el archivo antes de interpretarlo, sin contar el encabezado (C1).';
COMMENT ON COLUMN abet.archivo_origen.tipo_fuente IS 'BLACKBOARD_EXPORT (entrada normal) o R17_HISTORICO (migración de R-17 anteriores, H09 y H34).';

CREATE TABLE abet.carga (
    carga_id            integer     GENERATED ALWAYS AS IDENTITY,
    seccion_id          integer     NOT NULL,
    archivo_id          integer     NOT NULL,
    filas_de_datos      integer     NOT NULL,
    carrera_id          smallint    NOT NULL,
    conjunto_reglas_id  smallint    NOT NULL,
    estado              varchar(11) NOT NULL DEFAULT 'EN_CURSO',
    reemplaza_carga_id  integer     NULL,
    programa_version    varchar(40) NOT NULL,
    filas_leidas        integer     NOT NULL DEFAULT 0,
    filas_aceptadas     integer     NOT NULL DEFAULT 0,
    filas_rechazadas    integer     NOT NULL DEFAULT 0,
    iniciada_en         timestamptz NOT NULL DEFAULT now(),
    terminada_en        timestamptz NULL,
    CONSTRAINT pk_carga              PRIMARY KEY (carga_id),
    -- Clave extendida para que columnas y reemplazos repitan sección y carrera con FK compuestas.
    CONSTRAINT uq_carga_seccion      UNIQUE (carga_id, seccion_id, carrera_id),
    CONSTRAINT uq_carga_reemplaza    UNIQUE (reemplaza_carga_id),
    CONSTRAINT ck_carga_estado       CHECK (estado IN ('EN_CURSO', 'RECHAZADA', 'PUBLICADA', 'REEMPLAZADA')),
    CONSTRAINT ck_carga_filas        CHECK (filas_leidas >= 0 AND filas_aceptadas >= 0 AND filas_rechazadas >= 0
                                            AND filas_aceptadas + filas_rechazadas = filas_leidas),
    CONSTRAINT ck_carga_publicable   CHECK (estado IN ('EN_CURSO', 'RECHAZADA') OR filas_aceptadas > 0),
    -- Una carga publicada leyó todas las filas de datos del archivo, ni una más ni una menos (C1).
    CONSTRAINT ck_carga_conciliada   CHECK (estado IN ('EN_CURSO', 'RECHAZADA') OR filas_leidas = filas_de_datos),
    CONSTRAINT ck_carga_terminada    CHECK (estado = 'EN_CURSO' OR terminada_en IS NOT NULL),
    CONSTRAINT ck_carga_reemplaza    CHECK (reemplaza_carga_id IS NULL OR reemplaza_carga_id <> carga_id),
    CONSTRAINT fk_carga_seccion      FOREIGN KEY (seccion_id) REFERENCES abet.seccion (seccion_id),
    CONSTRAINT fk_carga_archivo      FOREIGN KEY (archivo_id, filas_de_datos)
                                     REFERENCES abet.archivo_origen (archivo_id, filas_de_datos),
    -- Las reglas de la carga son de la carrera de la carga, y sus columnas solo toman PI del plan de esa carrera.
    CONSTRAINT fk_carga_reglas       FOREIGN KEY (conjunto_reglas_id, carrera_id)
                                     REFERENCES abet.conjunto_reglas (conjunto_reglas_id, carrera_id),
    -- Solo se reemplaza una carga de la misma sección y carrera.
    CONSTRAINT fk_carga_reemplaza    FOREIGN KEY (reemplaza_carga_id, seccion_id, carrera_id)
                                     REFERENCES abet.carga (carga_id, seccion_id, carrera_id)
);
-- Una sola carga PUBLICADA por sección; para reemplazarla se marca antes la anterior como REEMPLAZADA.
-- Supone un archivo por sección con todos los SO medidos; si Blackboard entrega un archivo por SO (H51 abierto),
-- este grano cambia antes de la primera carga real. También supone una sola carrera por sección; un curso
-- compartido con PI de dos carreras queda bloqueado hasta decidir cómo se separan sus columnas (ver README).
CREATE UNIQUE INDEX uq_carga_publicada_por_seccion ON abet.carga (seccion_id) WHERE estado = 'PUBLICADA';
-- Un archivo alimenta a lo sumo una carga PUBLICADA. Tras un rechazo se reintenta, y una carga REEMPLAZADA
-- conserva su archivo, así el mismo archivo se reprocesa con reglas aprobadas o un programa corregido en una
-- carga nueva (EN_CURSO mientras la anterior sigue PUBLICADA) que la reemplaza (H57), sin editar
-- conjunto_reglas_id de la publicada.
CREATE UNIQUE INDEX uq_carga_archivo_util ON abet.carga (archivo_id) WHERE estado = 'PUBLICADA';
COMMENT ON TABLE abet.carga IS 'Intento de cargar un archivo en una sección con un conjunto de reglas; solo PUBLICADA alimenta las vistas.';
COMMENT ON COLUMN abet.carga.programa_version IS 'Versión (etiqueta git) del programa de carga que la ejecutó.';
COMMENT ON COLUMN abet.carga.reemplaza_carga_id IS 'Carga anterior de la misma sección que esta reemplaza (H57); la anterior pasa a REEMPLAZADA.';
COMMENT ON COLUMN abet.carga.filas_de_datos IS 'Copia de archivo_origen.filas_de_datos, atada por FK compuesta, para exigir filas_leidas = filas_de_datos al publicar.';
COMMENT ON COLUMN abet.carga.carrera_id IS 'Carrera dueña del conjunto de reglas y de los PI de la carga (H02).';

CREATE TABLE abet.carga_columna (
    carga_columna_id          integer       GENERATED ALWAYS AS IDENTITY,
    carga_id                  integer       NOT NULL,
    seccion_id                integer       NOT NULL,
    carrera_id                smallint      NOT NULL,
    periodo_id                smallint      NOT NULL,
    asignatura_id             integer       NOT NULL,
    plan_medicion_id          integer       NOT NULL,
    pi_id                     smallint      NOT NULL,
    pi_codigo                 varchar(5)    NOT NULL,
    posicion                  smallint      NOT NULL,
    encabezado                varchar(200)  NOT NULL,
    bb_columna_id             varchar(12)   NULL,
    puntaje_maximo_declarado  numeric(6, 2) NULL,
    CONSTRAINT pk_carga_columna           PRIMARY KEY (carga_columna_id),
    CONSTRAINT uq_carga_columna_pi        UNIQUE (carga_id, pi_id),
    CONSTRAINT uq_carga_columna_posicion  UNIQUE (carga_id, posicion),
    CONSTRAINT uq_carga_columna_extendida UNIQUE (carga_columna_id, carga_id, pi_id),
    CONSTRAINT uq_carga_columna_carga     UNIQUE (carga_columna_id, carga_id),
    CONSTRAINT ck_carga_columna_posicion  CHECK (posicion >= 1),
    CONSTRAINT ck_carga_columna_bb        CHECK (bb_columna_id ~ '^[0-9]{1,12}$'),
    CONSTRAINT ck_carga_columna_puntaje   CHECK (puntaje_maximo_declarado > 0),
    -- El encabezado empieza por el código exacto del PI seguido de « [», así «6.10 [» no pasa como 6.1 (C6).
    CONSTRAINT ck_carga_columna_encabezado CHECK (encabezado LIKE pi_codigo || ' [%'),
    -- La columna es de la misma sección y carrera que la carga, y la sección y el plan comparten periodo y asignatura.
    CONSTRAINT fk_carga_columna_carga     FOREIGN KEY (carga_id, seccion_id, carrera_id)
                                          REFERENCES abet.carga (carga_id, seccion_id, carrera_id),
    CONSTRAINT fk_carga_columna_seccion   FOREIGN KEY (seccion_id, periodo_id, asignatura_id)
                                          REFERENCES abet.seccion (seccion_id, periodo_id, asignatura_id),
    CONSTRAINT fk_carga_columna_plan      FOREIGN KEY (plan_medicion_id, periodo_id, asignatura_id, pi_id, carrera_id)
                                          REFERENCES abet.plan_medicion (plan_medicion_id, periodo_id, asignatura_id, pi_id, carrera_id),
    -- El código guardado es el del PI de la columna; un código que no está en el catálogo no entra.
    CONSTRAINT fk_carga_columna_pi_codigo FOREIGN KEY (pi_id, pi_codigo) REFERENCES abet.pi (pi_id, codigo)
);
COMMENT ON TABLE abet.carga_columna IS 'Columna del export reconocida como PI del plan de la misma asignatura y periodo (H32, C10).';
COMMENT ON COLUMN abet.carga_columna.encabezado IS 'Encabezado tal como viene, por ejemplo «5.1 [Total Pts: 4 Score] |<id>».';
COMMENT ON COLUMN abet.carga_columna.pi_codigo IS 'Código del PI con que empieza el encabezado; debe ser el código del pi_id.';
COMMENT ON COLUMN abet.carga_columna.bb_columna_id IS 'Id de la columna en Blackboard (el número tras «|» del encabezado).';
COMMENT ON COLUMN abet.carga_columna.puntaje_maximo_declarado IS 'Total Pts que declara el encabezado; se guarda aunque no coincida con la escala 1-4.';

CREATE TABLE abet.rechazo_fila (
    rechazo_id        integer     GENERATED ALWAYS AS IDENTITY,
    carga_id          integer     NOT NULL,
    fila_origen       integer     NULL,
    carga_columna_id  integer     NULL,
    motivo            varchar(30) NOT NULL,
    efecto            varchar(13) NOT NULL,
    CONSTRAINT pk_rechazo_fila          PRIMARY KEY (rechazo_id),
    CONSTRAINT ck_rechazo_fila_fila     CHECK (fila_origen >= 2),
    CONSTRAINT ck_rechazo_fila_motivo   CHECK (motivo IN (
        'CODIGO_VACIO', 'CODIGO_INVALIDO', 'CODIGO_DUPLICADO', 'NIVEL_FUERA_DE_ESCALA', 'NIVEL_NO_NUMERICO',
        'COLUMNA_PI_FUERA_DEL_PLAN', 'PI_DEL_PLAN_AUSENTE', 'ARCHIVO_SIN_FILAS', 'SECCION_NO_COINCIDE',
        'PUNTAJE_MAXIMO_DISTINTO')),
    CONSTRAINT ck_rechazo_fila_efecto   CHECK (efecto IN ('RECHAZA_FILA', 'RECHAZA_CARGA', 'AVISO')),
    CONSTRAINT ck_rechazo_fila_con_fila CHECK (efecto <> 'RECHAZA_FILA' OR fila_origen IS NOT NULL),
    CONSTRAINT fk_rechazo_fila_carga    FOREIGN KEY (carga_id) REFERENCES abet.carga (carga_id),
    -- La columna del rechazo es de la misma carga; un rechazo de archivo (sin columna) no se compara.
    CONSTRAINT fk_rechazo_fila_columna  FOREIGN KEY (carga_columna_id, carga_id)
                                        REFERENCES abet.carga_columna (carga_columna_id, carga_id)
);
CREATE INDEX ix_rechazo_fila_carga ON abet.rechazo_fila (carga_id);
COMMENT ON TABLE abet.rechazo_fila IS 'Motivo de rechazo o aviso por fila, columna o archivo; nunca guarda el valor leído (privacidad).';
COMMENT ON COLUMN abet.rechazo_fila.carga_columna_id IS 'Columna cuya celda causó el rechazo o el aviso; un RECHAZA_FILA descarta la fila completa, no solo esa celda.';
COMMENT ON COLUMN abet.rechazo_fila.efecto IS 'RECHAZA_FILA, RECHAZA_CARGA o AVISO (por ejemplo PUNTAJE_MAXIMO_DISTINTO cuando la columna declara 20 puntos).';
