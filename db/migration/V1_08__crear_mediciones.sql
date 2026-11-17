-- V1_08  Estudiante, fila aceptada del archivo y medición por estudiante y PI (solo DDL).
-- Cubre C4 y H28 (el código de estudiante es la clave de cada fila, sin cruce de nombres), C13 (código como
-- texto), H02 (carrera del estudiante como dimensión), H33 (grano estudiante x PI en una carga),
-- H71 (nivel original 1-4 sin transformar), H08 (estado SIN_EVIDENCIA) y C9 (sin duplicados por carga).

CREATE TABLE abet.estudiante (
    estudiante_id  integer    GENERATED ALWAYS AS IDENTITY,
    codigo         varchar(8) NOT NULL,
    carrera_id     smallint   NULL,
    CONSTRAINT pk_estudiante         PRIMARY KEY (estudiante_id),
    CONSTRAINT uq_estudiante_codigo  UNIQUE (codigo),
    CONSTRAINT ck_estudiante_codigo  CHECK (codigo ~ '^[0-9]{8}$'),
    CONSTRAINT fk_estudiante_carrera FOREIGN KEY (carrera_id) REFERENCES abet.carrera (carrera_id)
);
COMMENT ON TABLE abet.estudiante IS 'Solo el código institucional de 8 dígitos como texto; sin nombres (la carga descarta Last Name y First Name).';
COMMENT ON COLUMN abet.estudiante.carrera_id IS 'Carrera del estudiante; NULL hasta contar con la fuente oficial de matrícula (H02, H28). No guarda historia: con esa fuente pasa a una tabla por periodo.';

-- Cada fila aceptada del archivo es de un solo estudiante, y cada estudiante ocupa una sola fila por carga.
CREATE TABLE abet.carga_fila (
    carga_id       integer NOT NULL,
    fila_origen    integer NOT NULL,
    estudiante_id  integer NOT NULL,
    CONSTRAINT pk_carga_fila             PRIMARY KEY (carga_id, fila_origen),
    CONSTRAINT uq_carga_fila_estudiante  UNIQUE (carga_id, estudiante_id),
    -- Clave extendida para que la medición repita fila y estudiante con una FK compuesta.
    CONSTRAINT uq_carga_fila_extendida   UNIQUE (carga_id, fila_origen, estudiante_id),
    CONSTRAINT ck_carga_fila_fila        CHECK (fila_origen >= 2),
    CONSTRAINT fk_carga_fila_carga       FOREIGN KEY (carga_id) REFERENCES abet.carga (carga_id),
    CONSTRAINT fk_carga_fila_estudiante  FOREIGN KEY (estudiante_id) REFERENCES abet.estudiante (estudiante_id)
);
COMMENT ON TABLE abet.carga_fila IS 'Fila aceptada del archivo con el estudiante que identifica; las filas rechazadas van a rechazo_fila.';
COMMENT ON COLUMN abet.carga_fila.fila_origen IS 'Fila del archivo, contando el encabezado como fila 1; la consulta de control Q12 vigila que no pase de filas_de_datos + 1.';

CREATE TABLE abet.medicion (
    medicion_id       bigint      GENERATED ALWAYS AS IDENTITY,
    carga_id          integer     NOT NULL,
    carga_columna_id  integer     NOT NULL,
    pi_id             smallint    NOT NULL,
    estudiante_id     integer     NOT NULL,
    estado_evidencia  varchar(13) NOT NULL,
    nivel_original    smallint    NULL,
    fila_origen       integer     NOT NULL,
    CONSTRAINT pk_medicion              PRIMARY KEY (medicion_id),
    CONSTRAINT uq_medicion              UNIQUE (carga_id, pi_id, estudiante_id),
    CONSTRAINT uq_medicion_fila         UNIQUE (carga_columna_id, fila_origen),
    CONSTRAINT ck_medicion_estado       CHECK (estado_evidencia IN ('CALIFICADO', 'SIN_EVIDENCIA')),
    CONSTRAINT ck_medicion_nivel        CHECK (nivel_original BETWEEN 1 AND 4),
    CONSTRAINT ck_medicion_estado_nivel CHECK (
        (estado_evidencia = 'CALIFICADO'    AND nivel_original IS NOT NULL)
     OR (estado_evidencia = 'SIN_EVIDENCIA' AND nivel_original IS NULL)),
    CONSTRAINT ck_medicion_fila         CHECK (fila_origen >= 2),
    -- La columna pertenece a la misma carga y trae el mismo PI; la carga fija la sección.
    CONSTRAINT fk_medicion_columna      FOREIGN KEY (carga_columna_id, carga_id, pi_id)
                                        REFERENCES abet.carga_columna (carga_columna_id, carga_id, pi_id),
    -- La fila es de la misma carga y del mismo estudiante que la medición.
    CONSTRAINT fk_medicion_fila         FOREIGN KEY (carga_id, fila_origen, estudiante_id)
                                        REFERENCES abet.carga_fila (carga_id, fila_origen, estudiante_id)
);
CREATE INDEX ix_medicion_estudiante ON abet.medicion (estudiante_id);
COMMENT ON TABLE abet.medicion IS 'Nivel 1-4 que el docente registra en Blackboard para un estudiante y un PI en una carga (H33, H71).';
COMMENT ON COLUMN abet.medicion.estado_evidencia IS 'SIN_EVIDENCIA = celda vacía; cómo cuenta en el porcentaje lo decide la carrera (H08).';
COMMENT ON COLUMN abet.medicion.nivel_original IS 'Nivel entero 1-4. Un valor no entero (3,5) se redondearía al convertirlo a smallint; el programa de carga lo rechaza antes con NIVEL_NO_NUMERICO.';
COMMENT ON COLUMN abet.medicion.fila_origen IS 'Fila del archivo de origen, contando el encabezado como fila 1.';
