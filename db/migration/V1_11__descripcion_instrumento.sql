-- V1_11  Descripción del instrumento de medición en el plan de medición (solo DDL).
-- Cubre la spec 005, US-51, J-31 y AD-12 (BR-R17-11), que cierran J-27 de la spec 004. La descripción del instrumento
-- de cada PI del plan vive aquí, por periodo, asignatura y PI, porque abet.instrumento solo guarda el nombre, que
-- comparten 22 asignaturas. r17.py la lee y la escribe en G17:I19 del R-17, y deja vacía la celda de un PI sin ella.
-- La columna es nula, así que las filas que ya existen siguen cumpliendo y revertir el programa no exige revertir
-- esta migración. El texto lo carga db/datos/descripcion_instrumento_2026_2.sql, que en Neon corre Jefferson desde el
-- Windows (AD-20), y abet_app no la escribe, porque crear_rol_app.sql le da solo SELECT en abet.plan_medicion.
--
-- Blanco es lo mismo que en el Back, todo carácter para el que str.isspace() de Python es verdadero, que son los 29
-- puntos de código que quita str.strip(). La lista va escrita con escapes Unicode y no depende de la intercalación
-- ni de [[:space:]]. btrim con esa lista quita los blancos de los dos lados, así que la restricción exige que el texto
-- no cambie al quitarlos y que no quede vacío, es decir, al menos un carácter visible y ningún blanco a los lados.
-- 400 caracteres caben en G:I con las filas 17 a 19 de unos 76 puntos, y la descripción de la plantilla original
-- mide 263. Un texto más largo lo rechaza el largo de la columna (SQLSTATE 22001) antes de evaluar la restricción.

ALTER TABLE abet.plan_medicion
    ADD COLUMN descripcion_instrumento varchar(400) NULL,
    ADD CONSTRAINT ck_plan_medicion_descripcion CHECK (
        descripcion_instrumento <> ''
        AND descripcion_instrumento = btrim(descripcion_instrumento,
            U&'\0009\000A\000B\000C\000D\001C\001D\001E\001F\0020\0085\00A0\1680\2000\2001\2002\2003\2004\2005\2006\2007\2008\2009\200A\2028\2029\202F\205F\3000'));
COMMENT ON COLUMN abet.plan_medicion.descripcion_instrumento IS 'Descripción del instrumento de medición del PI en el periodo y la asignatura, que el R-17 escribe en G17:I19 (BR-R17-11); NULL si la Coordinación todavía no la fija (D-34).';
COMMENT ON CONSTRAINT ck_plan_medicion_descripcion ON abet.plan_medicion IS 'Al menos un carácter visible y ningún blanco a los lados, con los 29 blancos de str.isspace() de Python, la definición del Back (spec 005, US-51).';
