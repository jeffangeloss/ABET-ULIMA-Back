-- V1_04  Plan de medición: qué PI mide cada asignatura en cada periodo (solo DDL).
-- Cubre C2 y C10 (solo se leen como PI las columnas del plan), C7 (el PI pertenece a un SO que la
-- asignatura tributa en la misma versión de catálogo), H32 (ítem por PI ligado al plan) y H26 (la versión
-- del plan es la que catalogo_vigencia fija para la carrera en ese periodo, con una FK compuesta).
-- Las filas del plan son datos operativos y no van en migraciones.

CREATE TABLE abet.plan_medicion (
    plan_medicion_id     integer  GENERATED ALWAYS AS IDENTITY,
    periodo_id           smallint NOT NULL,
    asignatura_id        integer  NOT NULL,
    carrera_id           smallint NOT NULL,
    catalogo_version_id  smallint NOT NULL,
    so_id                smallint NOT NULL,
    pi_id                smallint NOT NULL,
    instrumento_id       smallint NULL,
    CONSTRAINT pk_plan_medicion            PRIMARY KEY (plan_medicion_id),
    CONSTRAINT uq_plan_medicion            UNIQUE (periodo_id, asignatura_id, pi_id),
    -- Clave extendida para que carga_columna no pueda apuntar al plan de otra asignatura, otro periodo u otra carrera.
    CONSTRAINT uq_plan_medicion_extendida  UNIQUE (plan_medicion_id, periodo_id, asignatura_id, pi_id, carrera_id),
    -- La versión del plan es la vigente para la carrera en el periodo.
    CONSTRAINT fk_plan_medicion_vigencia   FOREIGN KEY (periodo_id, carrera_id, catalogo_version_id)
                                           REFERENCES abet.catalogo_vigencia (periodo_id, carrera_id, catalogo_version_id),
    CONSTRAINT fk_plan_medicion_pi         FOREIGN KEY (pi_id, catalogo_version_id, so_id)
                                           REFERENCES abet.pi (pi_id, catalogo_version_id, so_id),
    CONSTRAINT fk_plan_medicion_asig_so    FOREIGN KEY (catalogo_version_id, asignatura_id, so_id)
                                           REFERENCES abet.asignatura_so (catalogo_version_id, asignatura_id, so_id),
    CONSTRAINT fk_plan_medicion_instrumento FOREIGN KEY (instrumento_id, catalogo_version_id)
                                           REFERENCES abet.instrumento (instrumento_id, catalogo_version_id)
);
COMMENT ON TABLE abet.plan_medicion IS 'PI que una asignatura mide en un periodo; el PI debe ser de un SO que la asignatura tributa en la versión vigente.';
COMMENT ON COLUMN abet.plan_medicion.carrera_id IS 'Carrera dueña del catálogo del PI; la carga solo aplica reglas de esa carrera.';
COMMENT ON COLUMN abet.plan_medicion.instrumento_id IS 'Instrumento del periodo; NULL si el catálogo no lo define (pares con «-»).';
