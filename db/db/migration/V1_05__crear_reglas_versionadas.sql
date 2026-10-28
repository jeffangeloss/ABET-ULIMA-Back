-- V1_05  Reglas de la carrera como parámetros versionados (solo DDL).
-- Cubre H03 (meta y nivel esperado versionados), H08 (trato del estudiante sin evidencia, pendiente),
-- H01 (conversión de 1-4 a 0-1, pendiente) y H57 (cada carga sabe con qué reglas se hizo).
-- Regla del proceso, que la base no impide sin disparadores. El programa no edita un conjunto APROBADO;
-- un cambio de regla crea un conjunto nuevo y las cargas pasan a él por reemplazo (H57).

CREATE TABLE abet.conjunto_reglas (
    conjunto_reglas_id  smallint     GENERATED ALWAYS AS IDENTITY,
    carrera_id          smallint     NOT NULL,
    version             varchar(30)  NOT NULL,
    estado              varchar(10)  NOT NULL DEFAULT 'BORRADOR',
    aprobado_por        varchar(120) NULL,
    aprobado_en         date         NULL,
    CONSTRAINT pk_conjunto_reglas          PRIMARY KEY (conjunto_reglas_id),
    CONSTRAINT uq_conjunto_reglas          UNIQUE (carrera_id, version),
    -- Clave extendida para que la carga use un conjunto de reglas de la carrera dueña de sus PI.
    CONSTRAINT uq_conjunto_reglas_carrera  UNIQUE (conjunto_reglas_id, carrera_id),
    CONSTRAINT ck_conjunto_reglas_estado   CHECK (estado IN ('BORRADOR', 'APROBADO')),
    CONSTRAINT ck_conjunto_reglas_aprobado CHECK (
        (estado = 'BORRADOR' AND aprobado_por IS NULL AND aprobado_en IS NULL)
     OR (estado = 'APROBADO' AND aprobado_por IS NOT NULL AND aprobado_en IS NOT NULL)),
    CONSTRAINT fk_conjunto_reglas_carrera  FOREIGN KEY (carrera_id) REFERENCES abet.carrera (carrera_id)
);
COMMENT ON TABLE abet.conjunto_reglas IS 'Versión del conjunto de reglas de una carrera; solo la carrera la pasa a APROBADO.';
COMMENT ON COLUMN abet.conjunto_reglas.aprobado_por IS 'Cargo o instancia que aprueba (por ejemplo el comité de la carrera), nunca el nombre de una persona.';

CREATE TABLE abet.parametro (
    clave        varchar(30)  NOT NULL,
    tipo         varchar(6)   NOT NULL,
    descripcion  varchar(300) NOT NULL,
    CONSTRAINT pk_parametro       PRIMARY KEY (clave),
    CONSTRAINT ck_parametro_clave CHECK (clave IN ('META_LOGRO', 'NIVEL_ESPERADO', 'CORTE_ROJO',
                                                   'CONVERSION_NIVEL_0_1', 'TRATO_SIN_EVIDENCIA')),
    CONSTRAINT ck_parametro_tipo  CHECK (tipo IN ('NUMERO', 'TEXTO', 'TABLA'))
);
COMMENT ON TABLE abet.parametro IS 'Lista cerrada de parámetros que la carrera debe fijar.';

CREATE TABLE abet.parametro_valor (
    conjunto_reglas_id  smallint      NOT NULL,
    clave               varchar(30)   NOT NULL,
    estado              varchar(9)    NOT NULL,
    valor_numero        numeric(9, 4) NULL,
    valor_texto         varchar(40)   NULL,
    CONSTRAINT pk_parametro_valor           PRIMARY KEY (conjunto_reglas_id, clave),
    -- Clave extendida para que la tabla hija exija un parámetro DEFINIDO.
    CONSTRAINT uq_parametro_valor_estado    UNIQUE (conjunto_reglas_id, clave, estado),
    CONSTRAINT ck_parametro_valor_estado    CHECK (estado IN ('DEFINIDO', 'PENDIENTE')),
    CONSTRAINT ck_parametro_valor_pendiente CHECK (estado = 'DEFINIDO' OR (valor_numero IS NULL AND valor_texto IS NULL)),
    -- Dominio por clave. Cada regla vale solo para su clave y solo cuando el parámetro está DEFINIDO.
    CONSTRAINT ck_parametro_valor_meta_logro CHECK (clave <> 'META_LOGRO' OR estado = 'PENDIENTE'
        OR (valor_numero IS NOT NULL AND valor_numero BETWEEN 0 AND 1 AND valor_texto IS NULL)),
    CONSTRAINT ck_parametro_valor_nivel_esperado CHECK (clave <> 'NIVEL_ESPERADO' OR estado = 'PENDIENTE'
        OR (valor_numero IS NOT NULL AND valor_numero IN (1, 2, 3, 4) AND valor_texto IS NULL)),
    CONSTRAINT ck_parametro_valor_corte_rojo CHECK (clave <> 'CORTE_ROJO' OR estado = 'PENDIENTE'
        OR (valor_numero IS NOT NULL AND valor_numero BETWEEN 0 AND 1 AND valor_texto IS NULL)),
    -- Parámetro de tipo tabla: nunca lleva valor escalar; sus filas viven en conversion_nivel_0_1.
    CONSTRAINT ck_parametro_valor_tabla CHECK (clave <> 'CONVERSION_NIVEL_0_1'
        OR (valor_numero IS NULL AND valor_texto IS NULL)),
    CONSTRAINT ck_parametro_valor_trato CHECK (clave <> 'TRATO_SIN_EVIDENCIA' OR estado = 'PENDIENTE'
        OR (valor_numero IS NULL AND valor_texto IN ('CUENTA_COMO_NO_LOGRADO', 'SE_EXCLUYE_DEL_DENOMINADOR'))),
    CONSTRAINT fk_parametro_valor_conjunto  FOREIGN KEY (conjunto_reglas_id) REFERENCES abet.conjunto_reglas (conjunto_reglas_id),
    CONSTRAINT fk_parametro_valor_parametro FOREIGN KEY (clave) REFERENCES abet.parametro (clave)
);
COMMENT ON TABLE abet.parametro_valor IS 'Valor de un parámetro en un conjunto de reglas; PENDIENTE no lleva valor.';
COMMENT ON COLUMN abet.parametro_valor.valor_numero IS 'META_LOGRO y CORTE_ROJO como proporción entre 0 y 1 (0,80 y no 80); NIVEL_ESPERADO entre 1 y 4.';

CREATE TABLE abet.conversion_nivel_0_1 (
    conjunto_reglas_id  smallint      NOT NULL,
    clave               varchar(30)   NOT NULL DEFAULT 'CONVERSION_NIVEL_0_1',
    estado              varchar(9)    NOT NULL DEFAULT 'DEFINIDO',
    nivel_original      smallint      NOT NULL,
    valor_0_1           numeric(5, 4) NOT NULL,
    CONSTRAINT pk_conversion_nivel_0_1        PRIMARY KEY (conjunto_reglas_id, nivel_original),
    CONSTRAINT ck_conversion_nivel_0_1_clave  CHECK (clave = 'CONVERSION_NIVEL_0_1'),
    CONSTRAINT ck_conversion_nivel_0_1_estado CHECK (estado = 'DEFINIDO'),
    CONSTRAINT ck_conversion_nivel_0_1_nivel  CHECK (nivel_original BETWEEN 1 AND 4),
    CONSTRAINT ck_conversion_nivel_0_1_valor  CHECK (valor_0_1 BETWEEN 0 AND 1),
    CONSTRAINT fk_conversion_nivel_0_1_valor  FOREIGN KEY (conjunto_reglas_id, clave, estado)
                                              REFERENCES abet.parametro_valor (conjunto_reglas_id, clave, estado)
);
COMMENT ON TABLE abet.conversion_nivel_0_1 IS 'Filas del parámetro CONVERSION_NIVEL_0_1; solo existen si el parámetro está DEFINIDO. Que estén los 4 niveles lo revisa una consulta de control.';
