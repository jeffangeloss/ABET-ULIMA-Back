-- V1_02  Catálogo curricular versionado (solo DDL).
-- Cubre H26 (todo lo curricular cuelga de una versión de catálogo), H21 y C6 (PI como texto «5.1»),
-- C7 (el SO sale del PI), C8 (ciclo de malla desde el catálogo), H23 (claves únicas),
-- H32 (rúbrica en el modelo), H35 (instrumento como lista cerrada) y H27 (estadío por asignatura y competencia).
-- catalogo_vigencia fija qué versión rige en cada periodo para cada carrera (H26), sin disparadores.

CREATE TABLE abet.catalogo_version (
    catalogo_version_id       smallint     GENERATED ALWAYS AS IDENTITY,
    carrera_id                smallint     NOT NULL,
    codigo                    varchar(30)  NOT NULL,
    estado                    varchar(10)  NOT NULL DEFAULT 'BORRADOR',
    vigente_desde_periodo_id  smallint     NULL,
    huella_fuente             char(64)     NULL,
    aprobado_por              varchar(120) NULL,
    aprobado_en               date         NULL,
    CONSTRAINT pk_catalogo_version          PRIMARY KEY (catalogo_version_id),
    CONSTRAINT uq_catalogo_version_codigo   UNIQUE (codigo),
    -- Clave extendida para que vigencia y plan de medición repitan la carrera con FK compuestas.
    CONSTRAINT uq_catalogo_version_carrera  UNIQUE (catalogo_version_id, carrera_id),
    CONSTRAINT ck_catalogo_version_codigo   CHECK (codigo ~ '^[A-Z]{2,10}-[0-9]{4}[A-Z0-9-]*$'),
    CONSTRAINT ck_catalogo_version_estado   CHECK (estado IN ('BORRADOR', 'APROBADA')),
    CONSTRAINT ck_catalogo_version_aprobada CHECK (estado = 'BORRADOR' OR vigente_desde_periodo_id IS NOT NULL),
    CONSTRAINT ck_catalogo_version_aprobacion CHECK (
        (estado = 'BORRADOR' AND aprobado_por IS NULL AND aprobado_en IS NULL)
     OR (estado = 'APROBADA' AND aprobado_por IS NOT NULL AND aprobado_en IS NOT NULL)),
    CONSTRAINT ck_catalogo_version_huella   CHECK (huella_fuente IS NULL OR huella_fuente ~ '^[0-9a-f]{64}$'),
    CONSTRAINT fk_catalogo_version_carrera  FOREIGN KEY (carrera_id) REFERENCES abet.carrera (carrera_id),
    CONSTRAINT fk_catalogo_version_periodo  FOREIGN KEY (vigente_desde_periodo_id) REFERENCES abet.periodo (periodo_id)
);
COMMENT ON TABLE abet.catalogo_version IS 'Versión del catálogo curricular de una carrera, por ejemplo AMB-2026 (H26).';
COMMENT ON COLUMN abet.catalogo_version.huella_fuente IS 'SHA-256 del JSON de referencia del que se generó la carga del catálogo.';
COMMENT ON COLUMN abet.catalogo_version.aprobado_por IS 'Cargo o instancia que aprueba la versión, nunca el nombre de una persona.';

CREATE TABLE abet.catalogo_vigencia (
    periodo_id           smallint NOT NULL,
    carrera_id           smallint NOT NULL,
    catalogo_version_id  smallint NOT NULL,
    -- Una sola versión por carrera y periodo.
    CONSTRAINT pk_catalogo_vigencia            PRIMARY KEY (periodo_id, carrera_id),
    -- Clave extendida para que plan_medicion apunte a la versión vigente de su carrera.
    CONSTRAINT uq_catalogo_vigencia_extendida  UNIQUE (periodo_id, carrera_id, catalogo_version_id),
    CONSTRAINT fk_catalogo_vigencia_periodo    FOREIGN KEY (periodo_id) REFERENCES abet.periodo (periodo_id),
    CONSTRAINT fk_catalogo_vigencia_version    FOREIGN KEY (catalogo_version_id, carrera_id)
                                               REFERENCES abet.catalogo_version (catalogo_version_id, carrera_id)
);
COMMENT ON TABLE abet.catalogo_vigencia IS 'Versión de catálogo que rige en un periodo para una carrera (H26); se registra antes del plan de medición del periodo.';

CREATE TABLE abet.so (
    so_id                smallint     GENERATED ALWAYS AS IDENTITY,
    catalogo_version_id  smallint     NOT NULL,
    numero               smallint     NOT NULL,
    descripcion          varchar(400) NOT NULL,
    CONSTRAINT pk_so            PRIMARY KEY (so_id),
    CONSTRAINT uq_so            UNIQUE (catalogo_version_id, numero),
    CONSTRAINT uq_so_version    UNIQUE (so_id, catalogo_version_id),
    CONSTRAINT uq_so_numero     UNIQUE (so_id, catalogo_version_id, numero),
    CONSTRAINT ck_so_numero     CHECK (numero BETWEEN 1 AND 20),
    CONSTRAINT fk_so_version    FOREIGN KEY (catalogo_version_id) REFERENCES abet.catalogo_version (catalogo_version_id)
);
COMMENT ON TABLE abet.so IS 'Resultado del estudiante (Student Outcome) dentro de una versión de catálogo.';

CREATE TABLE abet.pi (
    pi_id                smallint     GENERATED ALWAYS AS IDENTITY,
    catalogo_version_id  smallint     NOT NULL,
    so_id                smallint     NOT NULL,
    so_numero            smallint     NOT NULL,
    numero               smallint     NOT NULL,
    codigo               varchar(5)   NOT NULL,
    descripcion          varchar(300) NOT NULL,
    CONSTRAINT pk_pi              PRIMARY KEY (pi_id),
    CONSTRAINT uq_pi_codigo       UNIQUE (catalogo_version_id, codigo),
    CONSTRAINT uq_pi_numero       UNIQUE (so_id, numero),
    CONSTRAINT uq_pi_extendida    UNIQUE (pi_id, catalogo_version_id, so_id),
    -- Clave extendida para que carga_columna guarde el código del PI que reconoció en el encabezado.
    CONSTRAINT uq_pi_id_codigo    UNIQUE (pi_id, codigo),
    CONSTRAINT ck_pi_numero       CHECK (numero BETWEEN 1 AND 99),
    CONSTRAINT ck_pi_codigo       CHECK (codigo ~ '^[1-9][0-9]?\.[1-9][0-9]?$'),
    CONSTRAINT ck_pi_codigo_so    CHECK (codigo = CAST(so_numero AS varchar(2)) || '.' || CAST(numero AS varchar(2))),
    CONSTRAINT fk_pi_so           FOREIGN KEY (so_id, catalogo_version_id, so_numero)
                                  REFERENCES abet.so (so_id, catalogo_version_id, numero)
);
COMMENT ON TABLE abet.pi IS 'Indicador de desempeño. El código es texto SO.número, así 6.10 nunca colapsa en 6.1 (H21, C6).';
COMMENT ON COLUMN abet.pi.codigo IS 'Código de texto, por ejemplo 5.1; es el que aparece en el encabezado de Blackboard.';

CREATE TABLE abet.rubrica_nivel (
    pi_id       smallint     NOT NULL,
    nivel       smallint     NOT NULL,
    descriptor  varchar(800) NOT NULL,
    CONSTRAINT pk_rubrica_nivel    PRIMARY KEY (pi_id, nivel),
    CONSTRAINT ck_rubrica_nivel    CHECK (nivel IN (-1, 1, 2, 3, 4, 5)),
    CONSTRAINT fk_rubrica_nivel_pi FOREIGN KEY (pi_id) REFERENCES abet.pi (pi_id)
);
COMMENT ON TABLE abet.rubrica_nivel IS 'Descriptor de la rúbrica por PI y nivel, tal como la trae la plantilla (-1 y 1 a 5).';

CREATE TABLE abet.instrumento (
    instrumento_id       smallint    GENERATED ALWAYS AS IDENTITY,
    catalogo_version_id  smallint    NOT NULL,
    nombre               varchar(60) NOT NULL,
    CONSTRAINT pk_instrumento         PRIMARY KEY (instrumento_id),
    CONSTRAINT uq_instrumento         UNIQUE (catalogo_version_id, nombre),
    CONSTRAINT uq_instrumento_version UNIQUE (instrumento_id, catalogo_version_id),
    CONSTRAINT ck_instrumento_nombre  CHECK (nombre <> '-' AND nombre = btrim(nombre)),
    CONSTRAINT fk_instrumento_version FOREIGN KEY (catalogo_version_id) REFERENCES abet.catalogo_version (catalogo_version_id)
);
COMMENT ON TABLE abet.instrumento IS 'Lista cerrada de instrumentos de evaluación de una versión de catálogo (H35).';

CREATE TABLE abet.plan_estudios (
    catalogo_version_id  smallint NOT NULL,
    asignatura_id        integer  NOT NULL,
    ciclo_malla          smallint NOT NULL,
    CONSTRAINT pk_plan_estudios            PRIMARY KEY (catalogo_version_id, asignatura_id),
    CONSTRAINT ck_plan_estudios_ciclo      CHECK (ciclo_malla BETWEEN 1 AND 12),
    CONSTRAINT fk_plan_estudios_version    FOREIGN KEY (catalogo_version_id) REFERENCES abet.catalogo_version (catalogo_version_id),
    CONSTRAINT fk_plan_estudios_asignatura FOREIGN KEY (asignatura_id) REFERENCES abet.asignatura (asignatura_id)
);
COMMENT ON TABLE abet.plan_estudios IS 'Asignatura en la malla de una versión, con su ciclo (C8); nunca se deduce del número de sección.';

CREATE TABLE abet.asignatura_so (
    catalogo_version_id  smallint NOT NULL,
    asignatura_id        integer  NOT NULL,
    so_id                smallint NOT NULL,
    instrumento_id       smallint NULL,
    CONSTRAINT pk_asignatura_so             PRIMARY KEY (catalogo_version_id, asignatura_id, so_id),
    CONSTRAINT fk_asignatura_so_plan        FOREIGN KEY (catalogo_version_id, asignatura_id)
                                            REFERENCES abet.plan_estudios (catalogo_version_id, asignatura_id),
    CONSTRAINT fk_asignatura_so_so          FOREIGN KEY (so_id, catalogo_version_id)
                                            REFERENCES abet.so (so_id, catalogo_version_id),
    CONSTRAINT fk_asignatura_so_instrumento FOREIGN KEY (instrumento_id, catalogo_version_id)
                                            REFERENCES abet.instrumento (instrumento_id, catalogo_version_id)
);
COMMENT ON TABLE abet.asignatura_so IS 'SO que tributa cada asignatura en una versión; instrumento NULL donde la fuente trae «-».';

CREATE TABLE abet.competencia (
    competencia_id       smallint     GENERATED ALWAYS AS IDENTITY,
    catalogo_version_id  smallint     NOT NULL,
    codigo               varchar(3)   NOT NULL,
    nombre               varchar(120) NOT NULL,
    tipo                 varchar(10)  NOT NULL,
    CONSTRAINT pk_competencia          PRIMARY KEY (competencia_id),
    CONSTRAINT uq_competencia          UNIQUE (catalogo_version_id, codigo),
    CONSTRAINT uq_competencia_version  UNIQUE (competencia_id, catalogo_version_id),
    CONSTRAINT ck_competencia_codigo   CHECK (codigo ~ '^[GE][1-9][0-9]?$'),
    CONSTRAINT ck_competencia_tipo     CHECK ((tipo = 'GENERICA' AND codigo LIKE 'G%')
                                           OR (tipo = 'ESPECIFICA' AND codigo LIKE 'E%')),
    CONSTRAINT fk_competencia_version  FOREIGN KEY (catalogo_version_id) REFERENCES abet.catalogo_version (catalogo_version_id)
);
COMMENT ON TABLE abet.competencia IS 'Competencia genérica (G1 a G8) o específica (E1 a E3), con el código sin espacios.';

CREATE TABLE abet.competencia_so (
    catalogo_version_id  smallint NOT NULL,
    competencia_id       smallint NOT NULL,
    so_id                smallint NOT NULL,
    CONSTRAINT pk_competencia_so             PRIMARY KEY (competencia_id, so_id),
    CONSTRAINT fk_competencia_so_competencia FOREIGN KEY (competencia_id, catalogo_version_id)
                                             REFERENCES abet.competencia (competencia_id, catalogo_version_id),
    CONSTRAINT fk_competencia_so_so          FOREIGN KEY (so_id, catalogo_version_id)
                                             REFERENCES abet.so (so_id, catalogo_version_id)
);
COMMENT ON TABLE abet.competencia_so IS 'SO al que aporta una competencia de la misma versión; G1, G2, G5 y G7 no tienen fila.';

CREATE TABLE abet.asignatura_competencia (
    catalogo_version_id  smallint    NOT NULL,
    asignatura_id        integer     NOT NULL,
    competencia_id       smallint    NOT NULL,
    estadio              varchar(9)  NOT NULL,
    CONSTRAINT pk_asignatura_competencia             PRIMARY KEY (catalogo_version_id, asignatura_id, competencia_id),
    CONSTRAINT ck_asignatura_competencia_estadio     CHECK (estadio IN ('INICIAL', 'REFUERZO', 'LOGRADO')),
    CONSTRAINT fk_asignatura_competencia_plan        FOREIGN KEY (catalogo_version_id, asignatura_id)
                                                     REFERENCES abet.plan_estudios (catalogo_version_id, asignatura_id),
    CONSTRAINT fk_asignatura_competencia_competencia FOREIGN KEY (competencia_id, catalogo_version_id)
                                                     REFERENCES abet.competencia (competencia_id, catalogo_version_id)
);
COMMENT ON TABLE abet.asignatura_competencia IS 'Estadío (INICIAL, REFUERZO o LOGRADO) de una competencia en una asignatura de la malla (H27).';
