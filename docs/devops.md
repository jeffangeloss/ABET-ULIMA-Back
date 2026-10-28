# Ramas, versiones y entornos

Todo lo que hace falta para reproducir los entornos de prueba y de producción queda versionado en este repositorio, es decir el código, la CI, las migraciones (cuando la base pase a `db/`) y la configuración de despliegue. Los secretos no se versionan. Viven en Vercel, en los secretos de GitHub y en el `.env` local de cada persona, y `.env.example` lista sus nombres sin valores.

La configuración copia la de IQBF-ULIMA_Back y IQBF-ULIMA_Front con dos diferencias. La versión vive en el archivo `VERSION`, porque el lenguaje del backend todavía no está aprobado, y cada cambio actualiza `MEMORIA.md`.

## Ramas

| Rama | Sale de | Entra a | Despliegue |
|---|---|---|---|
| `main` | `develop` (versión) o `hotfix/*` | — | Producción (piloto con datos inventados) |
| `develop` (rama por defecto) | `main` al crearla | `main` por PR de versión | Vista previa |
| `feat/*`, `fix/*`, `docs/*`, `chore/*`, `test/*`, `refactor/*` | `develop` | `develop` por PR | Vista previa |
| `hotfix/*` | `main` | `main` por PR; después `main` vuelve a `develop` | Producción |

`main` y `develop` aceptan cambios solo por PR con el check `pruebas` en verde, y `main` exige además `flujo`. Ninguna de las dos admite empujes forzados ni borrado. Los PR se fusionan con rebase, sin commits de fusión.

## Publicar una versión

1. En una rama `chore/version-X.Y.Z` que sale de `develop`, cambiar `VERSION`, pasar la sección «Sin publicar» del `CHANGELOG.md` a `[X.Y.Z] - AAAA-MM-DD` y registrar la versión en `MEMORIA.md`. PR a `develop`.
2. Aplicar las migraciones nuevas de la base, primero en la rama de pruebas de Neon y luego en la principal, antes de fusionar el PR de versión.
3. PR de `develop` a `main` titulado «Versión X.Y.Z». Al fusionarlo, `release.yml` crea el tag `vX.Y.Z` y el Release con la sección del CHANGELOG.

Un arreglo urgente sale de `main` en `hotfix/*`, sube la versión de parche y vuelve a `develop` en cuanto llega a `main`.

## Controles de cada cambio

| Control | Dónde corre | Qué exige |
|---|---|---|
| `pruebas` | CI, en cada PR y en cada push a `develop` y `main` | `scripts/preflight.sh` sin fallas. Ninguna planilla, export ni respaldo fuera de `tests/datos_inventados/`, solo códigos de estudiante que empiezan con 99 dentro de esa carpeta, ningún `.env` versionado, ningún secreto con valor y, en un PR, `MEMORIA.md` actualizado. Las pruebas de la base, del backend y de aceptación se suman a este job cuando existan |
| `flujo` | CI, en cada PR a `main` | Que el origen sea `develop` o `hotfix/*` |
| `pre-commit` | En cada clon, activado con `git config core.hooksPath scripts/hooks` | La misma revisión sobre lo preparado, más `MEMORIA.md` dentro del commit |
| SonarQube Cloud y Snyk | CI, como checks informativos | Se agregan cuando Jefferson cree los proyectos y guarde los tokens como secretos del repositorio |

## Memoria del trabajo

`MEMORIA.md` es el punto de partida de cualquier persona o agente. Su «Punto actual» dice dónde quedó el trabajo y su «Registro» guarda una entrada por cambio, la más reciente primero, con lo probado en positivo y en negativo. `AGENTS.md` fija las reglas y el check `pruebas` las hace cumplir.

## Entornos

| Entorno | Código | Base de datos |
|---|---|---|
| Producción (piloto) | `main` | Neon, rama principal, solo datos inventados hasta la autorización de la universidad |
| Pruebas | `develop` | Neon, rama `develop`, solo datos inventados |
| CI | cada PR | PostgreSQL 16 desechable del runner |
| Local | cualquier rama | `abet_sis_med_dev` en la Mac |

Las variables de Producción y de Vista previa se separan en Vercel desde el primer despliegue, porque IQBF registra como pendiente que sus despliegues de vista previa apuntan a la base de producción.
