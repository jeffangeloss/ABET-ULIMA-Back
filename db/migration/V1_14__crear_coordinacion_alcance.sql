-- V1_14  Alcance de cada cuenta de coordinación, por carrera o por asignatura en un periodo (solo DDL, spec 008,
-- US-70, US-71, FR-008, BR-ACCESO-13 y J-49).
-- El rol COORDINADOR se conserva y ck_usuario_autorizado_rol no cambia (veredicto CAMBIAR del crítico de arquitectura).
-- Una fila de carrera da a la cuenta las secciones de las asignaturas del plan de estudios del catálogo vigente de esa
-- carrera en cada periodo, y una fila de asignatura, las secciones de esa asignatura en su periodo. Una cuenta
-- COORDINADOR sin filas no ve nada, y app/permisos.py une las filas de la cuenta. El periodo es obligatorio en la fila
-- de asignatura y nulo en la de carrera (valor provisional de J-49). uq_coordinacion_alcance usa NULLS NOT DISTINCT,
-- así la misma carrera no se repite para una cuenta aunque sus columnas de asignatura y periodo sean nulas.
-- Los datos no van aquí. db/datos/alcance_coordinacion_ambiental.sql da la carrera AMB a las coordinaciones que ya
-- existen, y db/herramientas/registrar_coordinacion.py registra la coordinación de un curso. El rol de la aplicación
-- solo lee esta tabla, con el SELECT que le da db/plataforma/neon/crear_rol_app.sql.

CREATE TABLE acceso.coordinacion_alcance (
    coordinacion_alcance_id  integer     GENERATED ALWAYS AS IDENTITY,
    usuario_id               integer     NOT NULL,
    carrera_id               smallint    NULL,
    asignatura_id            integer     NULL,
    periodo_id               smallint    NULL,
    asignado_en              timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_coordinacion_alcance            PRIMARY KEY (coordinacion_alcance_id),
    CONSTRAINT uq_coordinacion_alcance            UNIQUE NULLS NOT DISTINCT (usuario_id, carrera_id, asignatura_id, periodo_id),
    -- Exactamente una de carrera o asignatura.
    CONSTRAINT ck_coordinacion_alcance_uno        CHECK (num_nonnulls(carrera_id, asignatura_id) = 1),
    -- Periodo en la fila de asignatura y nulo en la de carrera (J-49).
    CONSTRAINT ck_coordinacion_alcance_periodo    CHECK ((asignatura_id IS NULL) = (periodo_id IS NULL)),
    CONSTRAINT fk_coordinacion_alcance_usuario    FOREIGN KEY (usuario_id) REFERENCES acceso.usuario_autorizado (usuario_id),
    CONSTRAINT fk_coordinacion_alcance_carrera    FOREIGN KEY (carrera_id) REFERENCES abet.carrera (carrera_id),
    CONSTRAINT fk_coordinacion_alcance_asignatura FOREIGN KEY (asignatura_id) REFERENCES abet.asignatura (asignatura_id),
    CONSTRAINT fk_coordinacion_alcance_periodo    FOREIGN KEY (periodo_id) REFERENCES abet.periodo (periodo_id)
);
COMMENT ON TABLE acceso.coordinacion_alcance IS 'Alcance de una cuenta COORDINADOR, por carrera o por asignatura en un periodo (spec 008, BR-ACCESO-13). Una cuenta COORDINADOR sin filas no ve ninguna sección, y el rol de la aplicación solo lee la tabla.';
COMMENT ON COLUMN acceso.coordinacion_alcance.carrera_id IS 'Carrera de la coordinación de carrera, que ve las secciones del plan de estudios del catálogo vigente de esa carrera en cada periodo; nulo en una fila de asignatura.';
COMMENT ON COLUMN acceso.coordinacion_alcance.asignatura_id IS 'Asignatura de la coordinación de un curso, que ve todas sus secciones en el periodo de la fila; nulo en una fila de carrera.';
COMMENT ON COLUMN acceso.coordinacion_alcance.periodo_id IS 'Periodo de la fila de asignatura, obligatorio en ella y nulo en la de carrera (J-49).';
