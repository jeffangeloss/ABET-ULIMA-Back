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
- Spec 002 de Capstone «plantilla de proyectos, tabla maestra en el formato nuevo y R-17 con la hoja Cursos Capstone»: 25 historias auditadas con 83 escenarios en Gherkin en español, FR-001 a FR-029, SC-001 a SC-013, decisiones D-14 a D-29 y J-11 a J-16, pendiente de aprobación de Jefferson (`specs/002-capstone/`).

### Seguridad

- Job `secretos` con gitleaks 8.30.1 fijado por suma SHA-256, y `.gitleaks.toml`.
- Dependabot para las acciones de GitHub, `.sonarcloud.properties` para SonarQube Cloud y `.snyk` con excepciones que vencen.
- `astral-sh/setup-uv` fijado por SHA en v10.3.0, con más de 14 días publicada, y Dependabot para `uv.lock`, con la misma espera de 14 días en las acciones y en los paquetes.
- Las pruebas de la base corren en un clúster de PostgreSQL desechable propio (`db/pruebas/cluster_desechable.sh`) y nunca en el de la Mac, después de que una prueba de mutación borrara la base local `abet_sis_med_dev` el 2026-10-28.
