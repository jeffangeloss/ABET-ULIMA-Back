-- Secciones de un periodo con plan de medición y sin profesor activo (spec 006, US-58, FR-011 y AD-04).
-- Consulta informativa de solo lectura, que no es un control de db/pruebas/pruebas.sql, porque la base de ese archivo
-- tiene a propósito dos secciones 301 sin profesor, que usan los casos de Q06 y Q07. Lista por asignatura y número
-- cada sección del periodo cuya asignatura tiene plan de medición en ese periodo y que no tiene en
-- acceso.docente_seccion ningún usuario activo con rol PROFESOR, y al final cuántas son. Una sección asignada solo a
-- un profesor dado de baja o solo a un coordinador aparece, porque ninguno de los dos sube su export (BR-ACCESO-08).
-- Se corre después de db/herramientas/cargar_programacion.py con --aplicar, y cada sección que devuelve va a la
-- Coordinación de Ambiental antes de la semana 15 (SC-006). La corre abet_respaldo, que lee abet y acceso desde
-- V1_09, o el usuario dueño de la base, desde el Windows de Jefferson.
--
--   psql -X -w -v ON_ERROR_STOP=1 -v periodo=2026-2 -f db/plataforma/neon/secciones_sin_docente.sql
--
-- La conexión llega por las variables de libpq, como en db/README.md. No escribe. La sesión pasa a solo lectura
-- antes de la primera consulta, así que no cambia nada aunque la corra el dueño. Sin la variable periodo, el script
-- se detiene antes de consultar.

\set ON_ERROR_STOP 1
\if :{?periodo}
\else
    \echo 'Falta el periodo, por ejemplo -v periodo=2026-2.'
    SELECT CAST('falta el periodo' AS integer);
\endif
SET default_transaction_read_only = on;
SHOW default_transaction_read_only;

\echo 'Secciones del periodo con plan de medición y sin profesor activo (asignatura y sección).'
SELECT a.codigo AS asignatura, s.numero AS seccion
FROM abet.seccion s
JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
WHERE pe.codigo = :'periodo'
  AND EXISTS (SELECT 1 FROM abet.plan_medicion pm
              WHERE pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id)
  AND NOT EXISTS (SELECT 1 FROM acceso.docente_seccion d
                  JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
                  WHERE d.seccion_id = s.seccion_id AND u.activo AND u.rol = 'PROFESOR')
ORDER BY a.codigo, CAST(s.numero AS integer);

\echo 'Cantidad de secciones con plan de medición y sin profesor activo.'
SELECT count(*) AS secciones_sin_docente
FROM abet.seccion s
JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id
WHERE pe.codigo = :'periodo'
  AND EXISTS (SELECT 1 FROM abet.plan_medicion pm
              WHERE pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id)
  AND NOT EXISTS (SELECT 1 FROM acceso.docente_seccion d
                  JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
                  WHERE d.seccion_id = s.seccion_id AND u.activo AND u.rol = 'PROFESOR');
