-- V1_15  Análisis por indicador de una carga, con su borrador y su declaración por PI (solo DDL, spec 005, US-47,
-- US-48, US-49, US-53, FR-004, J-38, J-39, J-40, AD-31 a AD-34, AD-36 y AD-56, BR-MEJORA-03 a BR-MEJORA-12).
-- La spec la llamaba V1_12, y pasa a V1_15 porque la spec 008 toma V1_12 a V1_14 (FR-004 de la spec 008).
--
-- Cuatro tablas, dos cabeceras por carga y dos hijas por PI (J-38). abet.mejora_borrador guarda una sola versión
-- por carga, que la ruta 15 sube en la misma transacción en que reemplaza los registros de abet.mejora_borrador_pi.
-- abet.mejora_declaracion es de solo INSERT, y la declaración vigente de una carga es la de mayor declaracion_id.
-- abet.mejora_declaracion_pi guarda por PI el tipo que fija el semáforo y la foto del logro, la meta y el semáforo
-- que vio el profesor (J-40). Las dos hijas tienen su clave foránea (carga_id, pi_id) a abet.carga_columna, que
-- uq_carga_columna_pi vuelve única, así que solo entran los PI que la carga mide. Ninguna tabla tiene columnas de
-- estado, responsable ni plazo (D-42), porque el estado PROPUESTA lo deriva la ruta 14.
--
-- Las causas y las acciones admiten hasta 800 caracteres (J-39) y rechazan, en las dos hijas, un número de
-- exactamente 8 dígitos no rodeado de otros dígitos o un correo (US-53), con el mismo patrón ASCII que la ruta y la
-- consulta de control Q16. Una columna nula pasa el CHECK, así que el borrador admite un campo vacío. En la
-- declaración, causa y acción son obligatorias y no en blanco, con los 29 blancos de str.isspace() de Python que usa
-- ck_plan_medicion_descripcion de V1_11 (BR-R17-11). La coherencia exige, con el semáforo presente, BUENA_PRACTICA
-- solo con VERDE y OPORTUNIDAD_MEJORA con AMBAR o ROJO (D-39), y la foto admite nulos por si D-39 o D-40 cambian.
-- Los permisos del rol de la aplicación los da db/plataforma/neon/crear_rol_app.sql, sin DELETE.

CREATE TABLE abet.mejora_borrador (
    carga_id         integer     NOT NULL,
    version          integer     NOT NULL,
    actualizado_en   timestamptz NOT NULL DEFAULT now(),
    actualizado_por  integer     NOT NULL,
    CONSTRAINT pk_mejora_borrador          PRIMARY KEY (carga_id),
    -- La versión 0 es la de una carga sin borrador, así que la primera fila guardada empieza en 1.
    CONSTRAINT ck_mejora_borrador_version  CHECK (version >= 1),
    CONSTRAINT fk_mejora_borrador_carga    FOREIGN KEY (carga_id) REFERENCES abet.carga (carga_id),
    CONSTRAINT fk_mejora_borrador_usuario  FOREIGN KEY (actualizado_por) REFERENCES acceso.usuario_autorizado (usuario_id)
);
COMMENT ON TABLE abet.mejora_borrador IS 'Cabecera del borrador del análisis por indicador de una carga, con una sola versión por carga (spec 005, US-48, BR-MEJORA-06).';
COMMENT ON COLUMN abet.mejora_borrador.version IS 'Versión del borrador, desde 1. La ruta 15 la sube en cada guardado y responde 409 si el cuerpo trae otra.';

CREATE TABLE abet.mejora_borrador_pi (
    carga_id  integer      NOT NULL,
    pi_id     smallint     NOT NULL,
    causa     varchar(800) NULL,
    accion    varchar(800) NULL,
    CONSTRAINT pk_mejora_borrador_pi             PRIMARY KEY (carga_id, pi_id),
    CONSTRAINT ck_mejora_borrador_pi_sin_codigos CHECK (
        causa !~ '(^|[^0-9])[0-9]{8}([^0-9]|$)|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+'
        AND accion !~ '(^|[^0-9])[0-9]{8}([^0-9]|$)|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+'),
    CONSTRAINT fk_mejora_borrador_pi_borrador    FOREIGN KEY (carga_id) REFERENCES abet.mejora_borrador (carga_id),
    CONSTRAINT fk_mejora_borrador_pi_columna     FOREIGN KEY (carga_id, pi_id) REFERENCES abet.carga_columna (carga_id, pi_id)
);
COMMENT ON TABLE abet.mejora_borrador_pi IS 'Causa y acción del borrador de cada PI que la carga mide, nulas mientras el profesor no las escribe (spec 005, US-47 y US-48).';

CREATE TABLE abet.mejora_declaracion (
    declaracion_id    integer     GENERATED ALWAYS AS IDENTITY,
    carga_id          integer     NOT NULL,
    version_borrador  integer     NOT NULL,
    declarada_en      timestamptz NOT NULL DEFAULT now(),
    declarada_por     integer     NOT NULL,
    CONSTRAINT pk_mejora_declaracion          PRIMARY KEY (declaracion_id),
    -- Clave extendida para que cada fila por PI repita la carga de su cabecera con una FK compuesta.
    CONSTRAINT uq_mejora_declaracion_carga    UNIQUE (declaracion_id, carga_id),
    CONSTRAINT ck_mejora_declaracion_version  CHECK (version_borrador >= 1),
    CONSTRAINT fk_mejora_declaracion_carga    FOREIGN KEY (carga_id) REFERENCES abet.carga (carga_id),
    CONSTRAINT fk_mejora_declaracion_usuario  FOREIGN KEY (declarada_por) REFERENCES acceso.usuario_autorizado (usuario_id)
);
COMMENT ON TABLE abet.mejora_declaracion IS 'Cabecera de cada declaración del análisis por indicador, de solo INSERT. La vigente de una carga es la de mayor declaracion_id (spec 005, US-47, US-49 y D-37).';
COMMENT ON COLUMN abet.mejora_declaracion.version_borrador IS 'Versión exacta del borrador que la ruta 16 declara.';

CREATE TABLE abet.mejora_declaracion_pi (
    declaracion_id  integer      NOT NULL,
    pi_id           smallint     NOT NULL,
    carga_id        integer      NOT NULL,
    tipo            varchar(18)  NOT NULL,
    causa           varchar(800) NOT NULL,
    accion          varchar(800) NOT NULL,
    logro_pct       numeric(4,1) NULL,
    meta_pct        numeric(4,1) NULL,
    semaforo        varchar(5)   NULL,
    CONSTRAINT pk_mejora_declaracion_pi             PRIMARY KEY (declaracion_id, pi_id),
    CONSTRAINT ck_mejora_declaracion_pi_tipo        CHECK (tipo IN ('OPORTUNIDAD_MEJORA', 'BUENA_PRACTICA')),
    CONSTRAINT ck_mejora_declaracion_pi_semaforo    CHECK (semaforo IN ('VERDE', 'AMBAR', 'ROJO')),
    -- Con la foto del semáforo, BUENA_PRACTICA va solo con VERDE y OPORTUNIDAD_MEJORA con AMBAR o ROJO (D-39).
    CONSTRAINT ck_mejora_declaracion_pi_coherencia  CHECK (semaforo IS NULL OR (tipo = 'BUENA_PRACTICA') = (semaforo = 'VERDE')),
    -- Al menos un carácter que no sea uno de los 29 blancos de V1_11.
    CONSTRAINT ck_mejora_declaracion_pi_texto       CHECK (
        btrim(causa, U&'\0009\000A\000B\000C\000D\001C\001D\001E\001F\0020\0085\00A0\1680\2000\2001\2002\2003\2004\2005\2006\2007\2008\2009\200A\2028\2029\202F\205F\3000') <> ''
        AND btrim(accion, U&'\0009\000A\000B\000C\000D\001C\001D\001E\001F\0020\0085\00A0\1680\2000\2001\2002\2003\2004\2005\2006\2007\2008\2009\200A\2028\2029\202F\205F\3000') <> ''),
    CONSTRAINT ck_mejora_declaracion_pi_sin_codigos CHECK (
        causa !~ '(^|[^0-9])[0-9]{8}([^0-9]|$)|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+'
        AND accion !~ '(^|[^0-9])[0-9]{8}([^0-9]|$)|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+'),
    -- La FK a la cabecera va primero, así que una fila con otra carga falla por ella antes que por la de la columna.
    CONSTRAINT fk_mejora_declaracion_pi_cabecera    FOREIGN KEY (declaracion_id, carga_id)
                                                    REFERENCES abet.mejora_declaracion (declaracion_id, carga_id),
    CONSTRAINT fk_mejora_declaracion_pi_columna     FOREIGN KEY (carga_id, pi_id) REFERENCES abet.carga_columna (carga_id, pi_id)
);
COMMENT ON TABLE abet.mejora_declaracion_pi IS 'Registro declarado de cada PI con calificados, con el tipo que fija el semáforo y la foto de lo que vio el profesor (spec 005, US-47, J-40 y D-39). Un PI sin calificaciones no tiene fila (D-40).';
COMMENT ON COLUMN abet.mejora_declaracion_pi.tipo IS 'OPORTUNIDAD_MEJORA si el PI no alcanza la meta (AMBAR o ROJO) y BUENA_PRACTICA si la alcanza (VERDE).';
COMMENT ON COLUMN abet.mejora_declaracion_pi.semaforo IS 'Foto del semáforo al declarar. Un cambio posterior de la meta no la cambia (J-40).';
