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
| `pruebas` | CI, en cada PR y en cada push a `develop` y `main` | `scripts/preflight.sh` sin fallas. Ninguna planilla, export ni respaldo fuera de `tests/datos_inventados/`, solo códigos de estudiante que empiezan con 99 dentro de esa carpeta, ningún `.env` versionado, ningún secreto con valor y, en un PR, `MEMORIA.md` actualizado. Además, `db/pruebas/correr_pruebas.sh` en un PostgreSQL 18 desechable (migraciones, rechazos de cada restricción y consultas de control Q01 a Q14) y `uv run --frozen pytest -q` con las dependencias exactas de `uv.lock`. Los pasos de aceptación (T050) entran en ese mismo pytest |
| `flujo` | CI, en cada PR a `main` | Que el origen sea `develop` o `hotfix/*` |
| `pre-commit` | En cada clon, activado con `git config core.hooksPath scripts/hooks` | La misma revisión sobre lo preparado, más `MEMORIA.md` dentro del commit |
| Hook `Stop` de Claude Code | `.claude/settings.json`, al final de cada turno de Claude | Si quedan cambios sin commit y `MEMORIA.md` no está entre ellos, Claude sigue trabajando hasta registrarlos (`scripts/recordar_memoria.sh`) |
| `secretos` | CI, en cada PR y push | gitleaks 8.30.1 sobre todo el historial, fijado por versión y suma SHA-256. Informativo hasta confirmar que no da falsos positivos |
| SonarQube Cloud | Análisis automático, configurado en `.sonarcloud.properties` | Calidad y seguridad del código nuevo con la puerta «Sonar way» |
| Snyk | Integración de Snyk con GitHub, con la política `.snyk` | Vulnerabilidades de las dependencias, con excepciones que vencen |
| Dependabot | `.github/dependabot.yml`, cada lunes | PR a `develop` con la versión nueva de cada acción de GitHub y su SHA |

Riesgo residual de la revisión previa. La regla 2 lee por contenido todo archivo de `tests/datos_inventados/`, sea cual sea su extensión, incluidos los textos en UTF-16 o Windows-1252, y falla con un contenedor OLE (por ejemplo un `.xls` binario) cuyo SHA-256 no esté en la lista fija `OLE_REVISADOS` de `scripts/preflight.sh`. La regla 1, en cambio, no incluye `.txt`, porque rompería `requirements.txt`. Un export real renombrado `.txt` y guardado fuera de `tests/datos_inventados/` no lo detiene ninguna de las dos reglas. Lo cubren la revisión humana del PR y gitleaks solo si el archivo trae un secreto, así que quien suba datos de prueba debe guardarlos en esa carpeta.

La revisión de seguridad de la spec 003 (2026-11-09) deja además cuatro límites de la revisión previa, que no cambian en ese PR. Con `--staged`, la regla 2 lee el archivo de la carpeta de trabajo y no la versión preparada para el commit, aunque la CI lo vuelve a revisar sobre el árbol del PR. Con `--pr`, la revisión mira el árbol final, así que un código real que un commit agrega y otro quita queda en la historia. De un zip lee solo las hojas y las cadenas compartidas, y no los comentarios, las cachés de tablas dinámicas ni un `.ods` o un `.xlsb`. Tampoco ve un contenido que no puede leer como texto, como un archivo comprimido con gzip o un número partido por separadores de miles.

## SonarQube Cloud, Snyk y secretos

Los tres controles siguen el modelo de IQBF y se refuerzan con gitleaks y Dependabot.

- **SonarQube Cloud.** El plan gratuito admite repos privados hasta 50 000 líneas por organización, y en IQBF ese límite ya detuvo el análisis el 18/10/2026. `.sonarcloud.properties` deja fuera lo que no se despliega para no gastar ese cupo. Como el plan gratuito solo analiza la rama principal y los PR hacia ella, la rama principal del proyecto en la consola debe ser `develop`. Cuando existan pruebas con cobertura, el análisis pasa a la CI con la acción oficial fijada por SHA y el secreto `SONAR_TOKEN`, y se apaga el análisis automático.
- **Snyk.** La integración con GitHub publica el estado `security/snyk` en cada commit, como en IQBF. Toda excepción en `.snyk` lleva la razón técnica, una fecha de vencimiento de seis meses como máximo y su fecha de creación. Snyk no lee `uv.lock` en el plan gratuito, así que el backend en Python exporta un `requirements.txt` para el análisis. El análisis de código de Snyk guarda el código en su región de Estados Unidos, lo que se acepta porque el código no lleva datos personales.
- **gitleaks.** El escaneo de secretos de GitHub en repos privados es de pago, y gitleaks es gratis en cuentas personales. `.gitleaks.toml` usa sus reglas por defecto y solo excluye `scripts/probar_preflight.sh`, que trae un secreto falso a propósito.
- **Dependabot.** Sus PR no escriben `MEMORIA.md`, así que la CI no les exige la memoria y la actualización se registra en el siguiente cambio.

Lo que hace Jefferson en las consolas, sin pasar ninguna credencial por un agente:

1. En SonarQube Cloud, importar los dos repos, cambiar la rama principal a `develop`, dejar la puerta «Sonar way» y fijar el código nuevo por versión anterior. Conviene una organización aparte para ABET, para no compartir el cupo de 50 000 líneas con IQBF.
2. En Snyk, importar los dos repos con la rama `develop`.
3. Instalar en los dos repos la aplicación de GitGuardian, como en IQBF, si quiere una segunda revisión de secretos en cada PR.

## Memoria del trabajo

`MEMORIA.md` es el punto de partida de cualquier persona o agente. Su «Punto actual» dice dónde quedó el trabajo y su «Registro» guarda una entrada por cambio, la más reciente primero, con lo probado en positivo y en negativo. `AGENTS.md` fija las reglas y el check `pruebas` las hace cumplir.

## Entornos

| Entorno | Código | Base de datos |
|---|---|---|
| Producción (piloto) | `main` | Neon, rama principal, solo datos inventados hasta la autorización de la universidad |
| Pruebas | `develop` | Neon, rama `develop`, solo datos inventados |
| CI | cada PR | PostgreSQL 18 desechable del runner |
| Local | cualquier rama | `abet_sis_med_dev` en la Mac |

Las variables de Producción y de Vista previa se separan en Vercel desde el primer despliegue, porque IQBF registra como pendiente que sus despliegues de vista previa apuntan a la base de producción.
