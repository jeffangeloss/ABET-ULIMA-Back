# Cambios

Los cambios visibles de este repositorio quedan aquí. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y las versiones siguen [SemVer](https://semver.org/lang/es/). La versión vigente está en `VERSION`.

## [Sin publicar]

### Agregado

- Ramas `main` y `develop` con la configuración de IQBF: `develop` por defecto, PR obligatorio, checks `pruebas` y `flujo`, sin empujes forzados ni borrado (`docs/devops.md`).
- CI con la revisión previa `scripts/preflight.sh` (datos inventados, secretos y memoria) y `release.yml`, que crea el tag y el Release desde este archivo.
- `MEMORIA.md` como memoria de trabajo, `AGENTS.md` con las reglas para personas y agentes, y el hook `pre-commit`.
- Hook `Stop` de Claude Code (`.claude/settings.json`) que no deja terminar un turno con cambios sin registrar en `MEMORIA.md`.
- Spec 001 del MVP «del export de Blackboard al R-17 desde la base»: constitución, 21 historias auditadas con 127 escenarios en Gherkin en español, plan por fases y tareas, aprobada por Jefferson en el chat el 2026-10-28.
- Base de datos en `db/` con su historia desde `jeffangeloss/ABET_ULIMA` (V1_01 a V1_08, las vistas R__ y sus pruebas), que el job `pruebas` corre en un PostgreSQL 16 desechable.
- Esqueleto de Python con uv (`pyproject.toml`, `uv.lock` y `requirements.txt` con hashes para Snyk), `.env.example` y pytest en el job `pruebas`, con la lectura del Gherkin en español por pytest-bdd.
- Generador determinista de los exports inventados de `tests/datos_inventados/` (`scripts/generar_exports_inventados.py`).
- Specs vivas de carga, R-17, acceso y periodo con 43 reglas BR (`specs/features/`), y los seis `.feature` del corte 1 definitivos, con 127 escenarios.
- V1_09 con el esquema `acceso` (usuarios autorizados, credenciales, sesiones, intentos fallidos, docentes por sección y códigos de acceso), el autor de cada carga, cuatro motivos nuevos de rechazo y el PI de los rechazos por PI; el rol de la aplicación con privilegio mínimo, las consultas de control de Neon, la guardia de datos inventados y los datos inventados de 2026-2, con sus pruebas.
- Escenarios del profesor con varias secciones de varias asignaturas (`varias_secciones.feature`, con 133 escenarios en siete archivos), sus datos inventados (`db/datos/varias_secciones_2026_2_inventado.sql`, solo en las bases desechables de las pruebas) y tres exports nuevos con su generador.
- Biblioteca `abet_carga` con el lector del export de Blackboard (revisión del zip, macros y vínculos externos), la validación de la estructura, la sección, el periodo y las filas, la carga en una sola transacción con su huella SHA-256, el R-17 desde `v_r17_por_pi` y la constancia de la carga.
- Plantilla vaciada del R-17 (`plantillas/R017_ambiental_general.xlsx`) con su logotipo aparte y su excepción en `.gitignore` y en `scripts/preflight.sh`.
- `app/permisos.py` con las secciones que ve cada rol y la regla única de quién sube y quién lee.
- Comando `python -m abet_carga` con los subcomandos `cargar` y `r17`, y el guion `scripts/demo_corte1.sh`, que corre la demo del corte 1 en un clúster desechable.
- API del corte 1 con FastAPI (`app/main.py`, `app/configuracion.py`, `app/sesion.py`, `app/rutas/`) y las cinco rutas del contrato, un solo 403 para lo ajeno y lo inexistente (propuesta), límite de intentos con candado por cuenta, `Cache-Control: no-store`, `scripts/asignar_clave.py`, `scripts/api_local.sh` y 81 pruebas en `tests/test_api_*.py`.
- `specs/001-mvp-carga-r17/audit.md` con el cruce de historia, escenario, prueba y resultado (91 aprobados, 15 omitidos y 27 pendientes de 133), la guía de la verificación a mano (T062) y la sección `Verification` fechada del 2026-10-30 en las cuatro specs vivas.

### Cambiado

- Escenarios del corte 1 ejecutables con pytest-bdd 9 en español contra la API y la base (`tests/aceptacion/pasos/`), con 170 aprobados y 19 omitidos con su razón, y la prueba de humo `e2e/humo.spec.ts` del Front con Playwright para Node como T053.

- Jefferson decide el 2026-10-28 dos puntos abiertos. J-06 adelanta en local el traslado de `bd/` a `db/` con git subtree, antes del primer `flyway migrate` en Neon y de V1_09, y J-10 suma el esquema `acceso` al respaldo diario de Neon sin los datos de `credencial`, `sesion`, `intento_fallido` ni `codigo_acceso`.

### Seguridad

- Job `secretos` con gitleaks 8.30.1 fijado por suma SHA-256, y `.gitleaks.toml`.
- Dependabot para las acciones de GitHub, `.sonarcloud.properties` para SonarQube Cloud y `.snyk` con excepciones que vencen.
- `astral-sh/setup-uv` fijado por SHA en v10.3.0, con más de 14 días publicada, y Dependabot para `uv.lock`, con la misma espera de 14 días en las acciones y en los paquetes.
- Las pruebas de la base corren en un clúster de PostgreSQL desechable propio (`db/pruebas/cluster_desechable.sh`) y nunca en el de la Mac, después de que una prueba de mutación borrara la base local `abet_sis_med_dev` el 2026-10-28.
- La guardia del clúster desechable (`tests/cluster_desechable.py` y `db/pruebas/cluster_desechable.sh`) reconoce la integración continua solo con `GITHUB_ACTIONS=true`, `RUNNER_TEMP` no vacío y un sistema distinto de macOS, así que exportar esa variable en la Mac no deja crear ni borrar bases en el clúster local. Las pruebas de Python también crean sus bases en ese clúster.
