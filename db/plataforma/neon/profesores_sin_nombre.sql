-- Secciones publicadas de un periodo con algún profesor asignado sin nombre (spec 010, US-98, FR-011).
-- Consulta informativa de solo lectura, que no es un control de db/pruebas/pruebas.sql ni de controles_neon.sql, porque un
-- profesor sin nombre es válido y el R-17 sale con D10 vacía mientras la carrera no entrega la hoja con los nombres
-- (D-58). Cuenta las secciones del periodo con una carga PUBLICADA y con al menos un usuario con rol PROFESOR asignado en
-- acceso.docente_seccion con el nombre nulo, y los profesores distintos sin nombre de esas secciones. Cuenta al profesor
-- dado de baja igual que el R-17, que no filtra por activo (J-67), y deja fuera a las cuentas COORDINADOR.
-- Se corre después de db/herramientas/cargar_programacion.py con la columna nombre, y debe dar 0 antes de entregar los
-- R-17 del periodo (SC-004). La corre abet_respaldo, que lee abet y acceso desde V1_09, o el usuario dueño de la base,
-- desde el Windows de Jefferson.
--
--   psql -X -w -v ON_ERROR_STOP=1 -v periodo=2026-1 -f db/plataforma/neon/profesores_sin_nombre.sql
--
-- La conexión llega por las variables de libpq, como en db/README.md. No escribe, y muestra solo dos números, sin
-- correos, nombres ni números de sección, para que su salida pueda pasar por un agente sin datos personales. La sesión
-- pasa a solo lectura antes de la primera consulta, así que no cambia nada aunque la corra el dueño. Sin la variable
-- periodo, el script se detiene antes de consultar.

\set ON_ERROR_STOP 1
\if :{?periodo}
\else
    \echo 'Falta el periodo, por ejemplo -v periodo=2026-1.'
    SELECT CAST('falta el periodo' AS integer);
\endif
SET default_transaction_read_only = on;
SHOW default_transaction_read_only;

\echo 'Secciones publicadas del periodo con algún profesor asignado sin nombre.'
SELECT count(DISTINCT s.seccion_id) AS secciones_con_profesor_sin_nombre
FROM abet.seccion s
JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id
JOIN abet.carga c ON c.seccion_id = s.seccion_id AND c.estado = 'PUBLICADA'
JOIN acceso.docente_seccion d ON d.seccion_id = s.seccion_id
JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
WHERE pe.codigo = :'periodo' AND u.rol = 'PROFESOR' AND u.nombre IS NULL;

\echo 'Profesores asignados sin nombre a esas secciones.'
SELECT count(DISTINCT u.usuario_id) AS profesores_sin_nombre
FROM abet.seccion s
JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id
JOIN abet.carga c ON c.seccion_id = s.seccion_id AND c.estado = 'PUBLICADA'
JOIN acceso.docente_seccion d ON d.seccion_id = s.seccion_id
JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
WHERE pe.codigo = :'periodo' AND u.rol = 'PROFESOR' AND u.nombre IS NULL;
