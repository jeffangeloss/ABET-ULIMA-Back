-- V1_10  Encabezado de PI con el prefijo del export real de Blackboard y motivo del export sin niveles (solo DDL).
-- Cubre la spec 003. US-26 y J-19: el export real nombra sus columnas de PI «ABET SO5.1 [Total Pts: 100 Score] |…» o
-- «ABET SO 5.3 […]», y el LIKE de V1_07 (pi_codigo || ' [%') las rechazaba aunque el programa de carga las
-- reconociera, así que la transacción entera caía en 500. US-36 y D-31: un export cuyas filas aceptadas no traen
-- ningún nivel en las columnas de los PI del plan queda RECHAZADO con SIN_CALIFICACIONES.
-- La regla del encabezado es la misma de _ENCABEZADO_DE_PI en abet_carga/lector.py: «ABET» opcional, luego «SO» o
-- «PI» opcional y luego el código exacto del PI seguido de «[», con cero a tres espacios entre las partes. Las letras
-- van en clases explícitas y los espacios son el espacio ASCII, para que la base no dependa de la intercalación ni
-- de [[:space:]] y acepte exactamente lo mismo que el lector. Se conserva la regla C6 de V1_07, porque después del
-- código solo pueden venir espacios y «[», así que «6.10 [» no pasa como 6.1. El patrón acepta todo lo que aceptaba
-- el LIKE, de modo que las filas que ya existen siguen cumpliendo y revertir el programa no exige revertir esta
-- migración. pi_codigo cumple ck_pi_codigo de V1_02, así que el punto es el único carácter que hay que escapar.
-- Las restricciones se reemplazan aquí y V1_07 y V1_09 no se editan. Nada de esta migración guarda nombres ni
-- valores leídos del archivo.

ALTER TABLE abet.carga_columna
    DROP CONSTRAINT ck_carga_columna_encabezado,
    ADD CONSTRAINT ck_carga_columna_encabezado CHECK (
        encabezado ~ ('^([Aa][Bb][Ee][Tt] {0,3})?(([Ss][Oo]|[Pp][Ii]) {0,3})?' || replace(pi_codigo, '.', '\.') || ' {0,3}\['));
COMMENT ON CONSTRAINT ck_carga_columna_encabezado ON abet.carga_columna IS 'El encabezado empieza por «ABET» opcional, «SO» o «PI» opcional y el código exacto del PI seguido de «[», con hasta tres espacios entre las partes, la misma regla del lector (spec 003, J-19); «6.10 [» no pasa como 6.1 (C6).';
COMMENT ON COLUMN abet.carga_columna.encabezado IS 'Encabezado tal como viene, por ejemplo «ABET SO5.1 [Total Pts: 100 Score] |<id>» o «5.1 [Total Pts: 4 Score] |<id>».';
COMMENT ON COLUMN abet.carga_columna.pi_codigo IS 'Código del PI que nombra el encabezado después de su prefijo; debe ser el código del pi_id.';

-- La lista de motivos de V1_09 más SIN_CALIFICACIONES, que el programa usa con RECHAZA_CARGA.
ALTER TABLE abet.rechazo_fila
    DROP CONSTRAINT ck_rechazo_fila_motivo,
    ADD CONSTRAINT ck_rechazo_fila_motivo CHECK (motivo IN (
        'CODIGO_VACIO', 'CODIGO_INVALIDO', 'CODIGO_DUPLICADO', 'NIVEL_FUERA_DE_ESCALA', 'NIVEL_NO_NUMERICO',
        'COLUMNA_PI_FUERA_DEL_PLAN', 'PI_DEL_PLAN_AUSENTE', 'ARCHIVO_SIN_FILAS', 'SECCION_NO_COINCIDE',
        'PUNTAJE_MAXIMO_DISTINTO', 'COLUMNA_CODIGO_AUSENTE', 'PI_REPETIDO', 'PERIODO_NO_COINCIDE',
        'SECCION_SIN_DECLARAR', 'SIN_CALIFICACIONES'));
COMMENT ON COLUMN abet.rechazo_fila.motivo IS 'Lista cerrada de motivos. El programa de carga usa RECHAZA_FILA con CODIGO_VACIO, CODIGO_INVALIDO, CODIGO_DUPLICADO, NIVEL_FUERA_DE_ESCALA y NIVEL_NO_NUMERICO; RECHAZA_CARGA con ARCHIVO_SIN_FILAS, PI_DEL_PLAN_AUSENTE, COLUMNA_CODIGO_AUSENTE, PI_REPETIDO, SECCION_NO_COINCIDE, PERIODO_NO_COINCIDE y SIN_CALIFICACIONES (V1_10); y AVISO con COLUMNA_PI_FUERA_DEL_PLAN, PUNTAJE_MAXIMO_DISTINTO y SECCION_SIN_DECLARAR. La base no ata el motivo al efecto.';
