-- V1_09  Esquema acceso, autor de cada carga y motivos nuevos de rechazo (solo DDL).
-- Cubre US-04 (usuarios autorizados con su rol y docentes por sección), US-05 (contraseña asignada como hash
-- Argon2id, sesión con el hash del token e intentos fallidos por correo), US-06 (visibilidad por docente_seccion),
-- US-16 y US-21 (carga.subida_por dice quién sube la carga o confirma su sección), US-12 y US-13
-- (COLUMNA_CODIGO_AUSENTE, PI_REPETIDO y PERIODO_NO_COINCIDE), US-20 (código de acceso del corte 2) y US-21
-- (SECCION_SIN_DECLARAR).
-- Los usuarios viven en acceso y no en abet porque guardan el correo, y la consulta de control Q04 vigila que abet
-- no tenga nombres ni datos de contacto. Ninguna tabla guarda en claro una contraseña, un token, un código ni el
-- correo de un intento fallido.
-- Con createSchemas = true, Flyway crea acceso antes de migrar cuando el entorno lo lista en schemas, aunque la base
-- ya tenga su historial, y lo anota como << Flyway Schema Creation >>. El CREATE SCHEMA IF NOT EXISTS de esta
-- migración, la única que crea un esquema, cubre el ensayo de Neon de db/pruebas/correr_pruebas.sh, que migra con
-- psql, y un entorno cuya lista schemas no trae acceso. Los permisos del rol de la aplicación viven en
-- db/plataforma/neon/crear_rol_app.sql.

CREATE SCHEMA IF NOT EXISTS acceso;
COMMENT ON SCHEMA acceso IS 'Usuarios autorizados, credenciales, sesiones, intentos fallidos de ingreso, docentes por sección y códigos de acceso (V1_09); el correo de usuario_autorizado es el único dato de contacto de la base.';

CREATE TABLE acceso.usuario_autorizado (
    usuario_id  integer      GENERATED ALWAYS AS IDENTITY,
    correo      varchar(254) NOT NULL,
    rol         varchar(11)  NOT NULL,
    activo      boolean      NOT NULL DEFAULT true,
    creado_en   timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT pk_usuario_autorizado        PRIMARY KEY (usuario_id),
    CONSTRAINT uq_usuario_autorizado_correo UNIQUE (correo),
    CONSTRAINT ck_usuario_autorizado_rol    CHECK (rol IN ('PROFESOR', 'COORDINADOR')),
    -- El correo se guarda normalizado, sin espacios a los lados, en minúscula y con una sola arroba, así que
    -- « Docente410@EXAMPLE.invalid » no entra como un usuario distinto de docente410@example.invalid.
    CONSTRAINT ck_usuario_autorizado_correo CHECK (correo = lower(btrim(correo))
                                                   AND correo ~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$')
);
COMMENT ON TABLE acceso.usuario_autorizado IS 'Persona autorizada a entrar al sistema, con su rol (US-04). Un usuario se da de baja con activo falso, nunca se borra.';
COMMENT ON COLUMN acceso.usuario_autorizado.correo IS 'Correo institucional normalizado (minúscula y sin espacios); la aplicación lo normaliza igual antes de compararlo (US-05).';
COMMENT ON COLUMN acceso.usuario_autorizado.rol IS 'PROFESOR actúa sobre las secciones de docente_seccion; COORDINADOR ve todas las secciones de la carrera.';
COMMENT ON COLUMN acceso.usuario_autorizado.activo IS 'Falso deja al usuario sin acceso; la aplicación lo lee en cada petición, así que su sesión abierta deja de servir.';

CREATE TABLE acceso.credencial (
    usuario_id      integer      NOT NULL,
    hash_clave      varchar(255) NOT NULL,
    actualizado_en  timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT pk_credencial         PRIMARY KEY (usuario_id),
    -- Solo un hash Argon2id en el formato de cadena PHC (Password Hashing Competition) que produce argon2-cffi,
    -- nunca el texto de la contraseña.
    CONSTRAINT ck_credencial_hash    CHECK (hash_clave ~ '^\$argon2id\$v=[0-9]+\$[^$[:space:]]+\$[A-Za-z0-9+/]+\$[A-Za-z0-9+/]+$'),
    CONSTRAINT fk_credencial_usuario FOREIGN KEY (usuario_id) REFERENCES acceso.usuario_autorizado (usuario_id)
);
COMMENT ON TABLE acceso.credencial IS 'Contraseña asignada de un usuario (US-05, J-03), solo como hash Argon2id. La asigna el administrador técnico con la conexión del dueño de la base, y el rol de la aplicación solo la lee.';
COMMENT ON COLUMN acceso.credencial.hash_clave IS 'Hash Argon2id en el formato de cadena PHC (Password Hashing Competition), $argon2id$v=19$m=...,t=...,p=...$sal$hash.';

CREATE TABLE acceso.sesion (
    sesion_id   bigint      GENERATED ALWAYS AS IDENTITY,
    usuario_id  integer     NOT NULL,
    hash_token  char(64)    NOT NULL,
    creada_en   timestamptz NOT NULL DEFAULT now(),
    expira_en   timestamptz NOT NULL DEFAULT now() + interval '12 hours',
    CONSTRAINT pk_sesion          PRIMARY KEY (sesion_id),
    CONSTRAINT uq_sesion_token    UNIQUE (hash_token),
    CONSTRAINT ck_sesion_token    CHECK (hash_token ~ '^[0-9a-f]{64}$'),
    -- Una sesión dura a lo sumo 12 horas, como la cookie abet_sesion. El cierre de sesión adelanta expira_en con
    -- least(expira_en, clock_timestamp()) y no borra la fila, porque el rol de la aplicación no borra. Sin least(),
    -- el cierre de una sesión ya vencida pasa el tope de 12 horas y esta restricción lo rechaza.
    CONSTRAINT ck_sesion_vigencia CHECK (expira_en > creada_en AND expira_en <= creada_en + interval '12 hours'),
    CONSTRAINT fk_sesion_usuario  FOREIGN KEY (usuario_id) REFERENCES acceso.usuario_autorizado (usuario_id)
);
COMMENT ON TABLE acceso.sesion IS 'Sesión abierta con la cookie abet_sesion (US-05). Guarda el hash del token, nunca el token.';
COMMENT ON COLUMN acceso.sesion.hash_token IS 'SHA-256 del token de la cookie, en hexadecimal minúscula.';
COMMENT ON COLUMN acceso.sesion.expira_en IS 'Fin de la sesión, creada_en más 12 horas por defecto, porque las dos columnas toman now() de la misma transacción y el rol de la aplicación inserta solo usuario_id y hash_token. El cierre de sesión fija expira_en = least(expira_en, clock_timestamp()), que deja igual una sesión ya vencida, porque una hora posterior a creada_en más 12 horas viola ck_sesion_vigencia.';

CREATE TABLE acceso.intento_fallido (
    intento_id    bigint      GENERATED ALWAYS AS IDENTITY,
    hash_cuenta   char(64)    NOT NULL,
    intentado_en  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_intento_fallido      PRIMARY KEY (intento_id),
    -- Hexadecimal minúscula, así el mismo correo da siempre el mismo hash y sus intentos se cuentan juntos.
    CONSTRAINT ck_intento_fallido_hash CHECK (hash_cuenta ~ '^[0-9a-f]{64}$')
);
CREATE INDEX ix_intento_fallido_cuenta ON acceso.intento_fallido (hash_cuenta, intentado_en);
COMMENT ON TABLE acceso.intento_fallido IS 'Intento fallido de ingreso con contraseña (US-05), exista o no un usuario con ese correo. El límite de 5 intentos en 15 minutos cuenta las filas de un mismo hash_cuenta, así que un correo desconocido y uno autorizado reciben la misma respuesta (FR-009), y el índice por hash y hora sostiene ese conteo. No lleva clave foránea, porque el correo puede no estar en usuario_autorizado, y el rol de la aplicación no borra, así que el dueño de la base retira las filas viejas cuando haga falta.';
COMMENT ON COLUMN acceso.intento_fallido.hash_cuenta IS 'Código de autenticación de mensajes basado en hash (hash-based message authentication code, HMAC) con SHA-256 del correo normalizado y el secreto de la aplicación, en hexadecimal minúscula, nunca el correo. El nombre evita la palabra correo porque la columna no guarda un dato de contacto, y así Q15 sigue encontrando solo usuario_autorizado.correo.';
COMMENT ON COLUMN acceso.intento_fallido.intentado_en IS 'Hora del intento, que pone la base, porque el rol de la aplicación inserta solo hash_cuenta.';

CREATE TABLE acceso.docente_seccion (
    docente_seccion_id  integer     GENERATED ALWAYS AS IDENTITY,
    usuario_id          integer     NOT NULL,
    seccion_id          integer     NOT NULL,
    asignado_en         timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pk_docente_seccion         PRIMARY KEY (docente_seccion_id),
    CONSTRAINT uq_docente_seccion         UNIQUE (usuario_id, seccion_id),
    CONSTRAINT fk_docente_seccion_usuario FOREIGN KEY (usuario_id) REFERENCES acceso.usuario_autorizado (usuario_id),
    CONSTRAINT fk_docente_seccion_seccion FOREIGN KEY (seccion_id) REFERENCES abet.seccion (seccion_id)
);
CREATE INDEX ix_docente_seccion_seccion ON acceso.docente_seccion (seccion_id);
COMMENT ON TABLE acceso.docente_seccion IS 'Sección que dicta un profesor (US-04 y US-06); admite más de un docente por sección. Es la fuente de la regla de visibilidad, y en el corte 1 solo el profesor asignado sube el export de la sección.';

CREATE TABLE acceso.codigo_acceso (
    codigo_acceso_id  bigint      GENERATED ALWAYS AS IDENTITY,
    usuario_id        integer     NOT NULL,
    hash_codigo       char(64)    NOT NULL,
    creado_en         timestamptz NOT NULL DEFAULT now(),
    expira_en         timestamptz NOT NULL DEFAULT now() + interval '10 minutes',
    intentos          smallint    NOT NULL DEFAULT 0,
    usado_en          timestamptz NULL,
    CONSTRAINT pk_codigo_acceso          PRIMARY KEY (codigo_acceso_id),
    CONSTRAINT ck_codigo_acceso_hash     CHECK (hash_codigo ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_codigo_acceso_vigencia CHECK (expira_en > creado_en AND expira_en <= creado_en + interval '10 minutes'),
    CONSTRAINT ck_codigo_acceso_intentos CHECK (intentos BETWEEN 0 AND 5),
    CONSTRAINT fk_codigo_acceso_usuario  FOREIGN KEY (usuario_id) REFERENCES acceso.usuario_autorizado (usuario_id)
);
CREATE INDEX ix_codigo_acceso_usuario ON acceso.codigo_acceso (usuario_id, creado_en);
COMMENT ON TABLE acceso.codigo_acceso IS 'Código de 6 dígitos que llega por correo en el corte 2 (US-20). Vence a los 10 minutos, sirve una sola vez y admite 5 intentos; el índice por usuario y hora sostiene el límite de pedidos.';
COMMENT ON COLUMN acceso.codigo_acceso.hash_codigo IS 'Hash del código en hexadecimal minúscula (por ejemplo HMAC-SHA256 con el secreto de la aplicación), nunca el código.';
COMMENT ON COLUMN acceso.codigo_acceso.usado_en IS 'Hora en que el código abre una sesión; un código usado no vuelve a servir.';

-- Quién sube cada carga. Admite NULL porque las cargas anteriores a V1_09 no lo registran.
ALTER TABLE abet.carga
    ADD COLUMN subida_por integer NULL,
    ADD CONSTRAINT fk_carga_subida_por FOREIGN KEY (subida_por) REFERENCES acceso.usuario_autorizado (usuario_id);
COMMENT ON COLUMN abet.carga.subida_por IS 'Usuario que sube la carga o confirma su sección (US-16 y US-21); NULL en las cargas anteriores a V1_09. Guarda el identificador y no el correo, así abet sigue sin datos de contacto (Q04).';

-- La lista de motivos de V1_07 más cuatro motivos nuevos. La restricción se reemplaza aquí y V1_07 no se edita.
ALTER TABLE abet.rechazo_fila
    DROP CONSTRAINT ck_rechazo_fila_motivo,
    ADD CONSTRAINT ck_rechazo_fila_motivo CHECK (motivo IN (
        'CODIGO_VACIO', 'CODIGO_INVALIDO', 'CODIGO_DUPLICADO', 'NIVEL_FUERA_DE_ESCALA', 'NIVEL_NO_NUMERICO',
        'COLUMNA_PI_FUERA_DEL_PLAN', 'PI_DEL_PLAN_AUSENTE', 'ARCHIVO_SIN_FILAS', 'SECCION_NO_COINCIDE',
        'PUNTAJE_MAXIMO_DISTINTO', 'COLUMNA_CODIGO_AUSENTE', 'PI_REPETIDO', 'PERIODO_NO_COINCIDE',
        'SECCION_SIN_DECLARAR'));
COMMENT ON COLUMN abet.rechazo_fila.motivo IS 'Lista cerrada de motivos. El programa de carga usa RECHAZA_FILA con CODIGO_VACIO, CODIGO_INVALIDO, CODIGO_DUPLICADO, NIVEL_FUERA_DE_ESCALA y NIVEL_NO_NUMERICO; RECHAZA_CARGA con ARCHIVO_SIN_FILAS, PI_DEL_PLAN_AUSENTE, COLUMNA_CODIGO_AUSENTE, PI_REPETIDO, SECCION_NO_COINCIDE y PERIODO_NO_COINCIDE; y AVISO con COLUMNA_PI_FUERA_DEL_PLAN, PUNTAJE_MAXIMO_DISTINTO y SECCION_SIN_DECLARAR. La base no ata el motivo al efecto.';

-- El PI del plan que falta en el export (PI_DEL_PLAN_AUSENTE) o que el export repite (PI_REPETIDO). Con él, la
-- constancia leída después nombra el mismo PI que la respuesta de la subida (BR-R17-10). Admite NULL por los demás
-- motivos y por los rechazos anteriores a V1_09, que no lo registran.
ALTER TABLE abet.rechazo_fila
    ADD COLUMN pi_id smallint NULL,
    ADD CONSTRAINT fk_rechazo_fila_pi FOREIGN KEY (pi_id) REFERENCES abet.pi (pi_id),
    ADD CONSTRAINT ck_rechazo_fila_pi CHECK (pi_id IS NULL OR motivo IN ('PI_DEL_PLAN_AUSENTE', 'PI_REPETIDO'));
COMMENT ON COLUMN abet.rechazo_fila.pi_id IS 'PI del plan que falta (PI_DEL_PLAN_AUSENTE) o que se repite (PI_REPETIDO). Desde V1_09 el programa de carga lo guarda en esos dos motivos, y ningún otro motivo lo admite (ck_rechazo_fila_pi).';
