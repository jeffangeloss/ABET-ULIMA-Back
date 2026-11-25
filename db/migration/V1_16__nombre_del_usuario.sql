-- V1_16  Nombre opcional del usuario autorizado, para el valor «Profesor:» del R-17 (solo DDL).
-- Cubre US-95 de la spec 010 (BR-ACCESO-15). La columna vive en acceso y no en abet, porque Q04 prohíbe columnas de
-- nombre de persona en las tablas de abet y los roles de lectura abet_lectura y powerbi_lectura no alcanzan acceso.
-- Es opcional, así que los usuarios que ya existen quedan con el nombre nulo y siguen siendo válidos, y la base no
-- normaliza el nombre sino que lo exige normalizado, porque la capitalización de un apellido compuesto no se adivina.
-- Los nombres reales entran solo por db/herramientas/cargar_programacion.py, desde el Windows de Jefferson, y git lleva
-- solo nombres inventados.

ALTER TABLE acceso.usuario_autorizado
    ADD COLUMN nombre varchar(120) NULL,
    -- Un nombre nulo cumple todas las condiciones. Uno que no es nulo se guarda recortado, sin dobles espacios, sin
    -- caracteres de control (los ASCII por [[:cntrl:]] y los de C1 por \u0080 a \u009F, que no dependen del
    -- locale) ni de formato invisibles (U+00AD, U+200B a U+200F, U+202A a U+202E, U+2060 a U+2064 y U+FEFF), sin
    -- arroba ni dígitos, para que un correo o un código no pase por nombre, sin coma, porque la coma separa a los
    -- profesores en D10 del R-17 (J-68), y en la forma de normalización canónica compuesta de Unicode (NFC), para
    -- que «Á» se guarde siempre igual.
    ADD CONSTRAINT ck_usuario_autorizado_nombre CHECK (
        nombre = btrim(nombre)
        AND nombre <> ''
        AND nombre !~ '  '
        AND nombre !~ '[[:cntrl:]\u0080-\u009F]'
        AND nombre !~ '[­​-‏‪-‮⁠-⁤﻿]'
        AND nombre !~ '[@,0-9]'
        AND nombre IS NFC NORMALIZED);

COMMENT ON SCHEMA acceso IS 'Usuarios autorizados, credenciales, sesiones, intentos fallidos de ingreso, docentes por sección y códigos de acceso (V1_09); el correo y el nombre opcional de usuario_autorizado (V1_16) son los únicos datos de contacto y de persona de la base.';
COMMENT ON COLUMN acceso.usuario_autorizado.nombre IS 'Nombre del usuario tal como lo escribe la carrera, opcional (nulo en las cuentas COORDINADOR y en los usuarios sin cargar), de hasta 120 caracteres, recortado, sin dobles espacios, sin coma, arroba ni dígitos y en NFC (ck_usuario_autorizado_nombre). Es un dato personal de la Ley 29733 y su reglamento, el DS 016-2024-JUS, y solo sale en D10 de la hoja «Cursos de Carrera» del R-17 (spec 010). Lo carga cargar_programacion.py y la aplicación solo lo lee.';
