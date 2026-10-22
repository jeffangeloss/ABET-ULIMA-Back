-- V1_01  Organización mínima para ubicar una medición (solo DDL).
-- Cubre H02 (facultad y carrera desde el primer esquema), H32 (clave de sección y curso de Blackboard)
-- y C13 (sección = periodo + asignatura + número, nunca solo el número).
-- El esquema abet lo crea Flyway (schemas = ["abet"] en el entorno y createSchemas = true).

CREATE TABLE abet.facultad (
    facultad_id  smallint     GENERATED ALWAYS AS IDENTITY,
    codigo       varchar(10)  NOT NULL,
    nombre       varchar(120) NOT NULL,
    CONSTRAINT pk_facultad        PRIMARY KEY (facultad_id),
    CONSTRAINT uq_facultad_codigo UNIQUE (codigo),
    CONSTRAINT uq_facultad_nombre UNIQUE (nombre),
    CONSTRAINT ck_facultad_codigo CHECK (codigo ~ '^[A-Z]{2,10}$')
);
COMMENT ON TABLE abet.facultad IS 'Facultad que agrupa carreras (H02).';

CREATE TABLE abet.carrera (
    carrera_id   smallint     GENERATED ALWAYS AS IDENTITY,
    facultad_id  smallint     NOT NULL,
    codigo       varchar(10)  NOT NULL,
    nombre       varchar(120) NOT NULL,
    CONSTRAINT pk_carrera          PRIMARY KEY (carrera_id),
    CONSTRAINT uq_carrera_codigo   UNIQUE (codigo),
    CONSTRAINT uq_carrera_nombre   UNIQUE (nombre),
    CONSTRAINT ck_carrera_codigo   CHECK (codigo ~ '^[A-Z]{2,10}$'),
    CONSTRAINT fk_carrera_facultad FOREIGN KEY (facultad_id) REFERENCES abet.facultad (facultad_id)
);
COMMENT ON TABLE abet.carrera IS 'Carrera acreditada o que dicta asignaturas (H02).';

CREATE TABLE abet.periodo (
    periodo_id  smallint    GENERATED ALWAYS AS IDENTITY,
    anio        smallint    NOT NULL,
    ciclo       smallint    NOT NULL,
    codigo      varchar(6)  NOT NULL,
    CONSTRAINT pk_periodo          PRIMARY KEY (periodo_id),
    CONSTRAINT uq_periodo          UNIQUE (anio, ciclo),
    CONSTRAINT uq_periodo_codigo   UNIQUE (codigo),
    CONSTRAINT ck_periodo_anio     CHECK (anio BETWEEN 2020 AND 2100),
    CONSTRAINT ck_periodo_ciclo    CHECK (ciclo BETWEEN 0 AND 2),
    CONSTRAINT ck_periodo_codigo   CHECK (codigo = CAST(anio AS varchar(4)) || '-' || CAST(ciclo AS varchar(1)))
);
COMMENT ON TABLE abet.periodo IS 'Periodo académico con código AAAA-C, por ejemplo 2026-2 (ciclo 0 reservado para verano).';

CREATE TABLE abet.asignatura (
    asignatura_id  integer      GENERATED ALWAYS AS IDENTITY,
    codigo         varchar(6)   NOT NULL,
    nombre         varchar(150) NOT NULL,
    CONSTRAINT pk_asignatura        PRIMARY KEY (asignatura_id),
    CONSTRAINT uq_asignatura_codigo UNIQUE (codigo),
    CONSTRAINT ck_asignatura_codigo CHECK (codigo ~ '^[0-9]{4}([0-9]{2})?$')
);
COMMENT ON TABLE abet.asignatura IS 'Asignatura por código institucional de 4 o 6 dígitos, siempre como texto.';

CREATE TABLE abet.seccion (
    seccion_id        integer      GENERATED ALWAYS AS IDENTITY,
    periodo_id        smallint     NOT NULL,
    asignatura_id     integer      NOT NULL,
    numero            varchar(5)   NOT NULL,
    curso_blackboard  varchar(100) NULL,
    CONSTRAINT pk_seccion            PRIMARY KEY (seccion_id),
    CONSTRAINT uq_seccion            UNIQUE (periodo_id, asignatura_id, numero),
    -- Clave extendida para que carga y columna repitan periodo y asignatura con FK compuestas.
    CONSTRAINT uq_seccion_extendida  UNIQUE (seccion_id, periodo_id, asignatura_id),
    CONSTRAINT uq_seccion_curso_bb   UNIQUE (curso_blackboard),
    -- Sin ceros a la izquierda, para que «0410» y «410» no pasen como dos secciones distintas.
    CONSTRAINT ck_seccion_numero     CHECK (numero ~ '^[1-9][0-9]{0,4}$'),
    CONSTRAINT fk_seccion_periodo    FOREIGN KEY (periodo_id) REFERENCES abet.periodo (periodo_id),
    CONSTRAINT fk_seccion_asignatura FOREIGN KEY (asignatura_id) REFERENCES abet.asignatura (asignatura_id)
);
COMMENT ON TABLE abet.seccion IS 'Sección identificada por periodo + asignatura + número, nunca solo por número (C13, H32).';
COMMENT ON COLUMN abet.seccion.numero IS 'Número de sección como texto, sin ceros a la izquierda; el mismo número se repite en otras asignaturas.';
COMMENT ON COLUMN abet.seccion.curso_blackboard IS 'Identificador del curso en Blackboard cuando se conoce (H32).';
