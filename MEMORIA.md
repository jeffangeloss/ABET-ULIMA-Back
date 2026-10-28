# Memoria de ABET-ULIMA-Back

Este archivo es la memoria de trabajo del repositorio. Lo lee primero cualquier persona o agente que retome el trabajo, y se actualiza en el mismo commit de cada cambio (`AGENTS.md`, regla 2). El hook `pre-commit` y el check `pruebas` rechazan un cambio que no lo actualiza.

## Cómo se usa

1. Antes de empezar, leer «Punto actual».
2. Al terminar un cambio y antes del commit, actualizar «Punto actual» y agregar una entrada al comienzo del «Registro» con la plantilla de abajo.
3. Una entrada anterior no se borra ni se reescribe. Una corrección se registra como entrada nueva que cita la anterior por su fecha y título.
4. El commit de cada entrada se encuentra con `git log -- MEMORIA.md`.
5. Nunca se copian credenciales, datos personales ni nombres o códigos de estudiantes reales.

## Punto actual

- **Fecha**: 2026-10-28
- **Rama de trabajo**: `chore/seguridad-y-memoria`, en PR a `develop`
- **Versión publicada**: ninguna (`VERSION` = 0.0.0)
- **Último cambio**: hook de memoria para Claude Code, gitleaks, Dependabot y la configuración de SonarQube Cloud y Snyk
- **En curso**: plan del MVP (carga del export de Blackboard, datos en Neon y R-17), en revisión por Jefferson
- **Siguiente paso**: fusionar este PR, aprobar el plan del MVP y abrir su spec en `specs/` por PR a `develop`
- **Bloqueos**: el proyecto de Neon (aws-sa-east-1) todavía no existe; SonarQube Cloud y Snyk esperan que Jefferson importe los repos en sus consolas (`docs/devops.md`)
- **Repos relacionados**: `jeffangeloss/ABET-ULIMA-Front` (pantallas) y `jeffangeloss/ABET_ULIMA` (base con Flyway, pasa a `db/` de este repo)

## Plantilla de una entrada

```
### AAAA-MM-DD HH:MM (Lima) · <rama> · <título corto>
- Quién: persona o agente; subagentes que participaron y qué verificó cada uno
- Qué cambió: archivos y efecto
- Por qué: historia (US-NN), regla (BR-XXX-NN) o pedido
- Lo que debe hacer, cómo se probó: comando y resultado
- Lo que no debe hacer, cómo se probó: caso negativo, comando y resultado
- Correcciones: errores encontrados y cómo se resolvieron
- Cómo se reporta: PR, CHANGELOG, audit.md o constancia
- Pendiente y siguiente paso
```

## Registro

### 2026-10-28 14:10 (Lima) · chore/seguridad-y-memoria · Hook de memoria, secretos, SonarQube Cloud y Snyk

- **Quién**: Claude Code, a pedido de Jefferson («todos los cambios que se hagan deben quedar documentados en un archivo de memoria … siempre luego de cada cambio» e «implementa buenas prácticas de uso de SonarQube y Snyk»). Un flujo de cuatro investigadores con un verificador cada uno revisó SonarQube Cloud, Snyk, la seguridad de GitHub en repos privados y las skills de DevOps; los verificadores corrigieron datos de planes y confirmaron los 8 SHA de acciones contra sus tags.
- **Qué cambió**: `.claude/settings.json` con un hook `Stop` que llama a `scripts/recordar_memoria.sh`; job `secretos` en `ci.yml` con gitleaks 8.30.1 fijado por suma SHA-256 y `.gitleaks.toml`; `.github/dependabot.yml` para las acciones; `.sonarcloud.properties` y `.snyk` con las convenciones de IQBF; excepción de la regla de memoria para los PR de Dependabot; sección «SonarQube Cloud, Snyk y secretos» en `docs/devops.md`.
- **Por qué**: que la memoria se actualice siempre, también dentro de las sesiones de Claude, y blindar el repositorio con análisis de código, dependencias y secretos (pedido de Jefferson del 28/10/2026).
- **Lo que debe hacer, cómo se probó**: `bash scripts/probar_preflight.sh` da «19 bien, 0 mal». El hook no bloquea con el repositorio limpio, con `MEMORIA.md` entre los cambios ni la segunda vez seguida (`stop_hook_active`). `jq -e` confirma que `.claude/settings.json` declara el hook. La corrida del job `secretos` en este PR muestra si gitleaks pasa sobre el historial.
- **Lo que no debe hacer, cómo se probó**: el hook bloquea con salida 2 un cambio sin `MEMORIA.md` y un archivo nuevo sin `MEMORIA.md`; fuera de un repositorio git no bloquea ni falla.
- **Correcciones**: ninguna en esta entrada.
- **Cómo se reporta**: este registro, `CHANGELOG.md` («Sin publicar») y los checks `pruebas` y `secretos` del PR.
- **Pendiente y siguiente paso**: Jefferson importa los repos en SonarQube Cloud y Snyk; decidir si `secretos` pasa a check requerido y si se activan el requisito de acciones fijadas por SHA y las alertas de Dependabot.

### 2026-10-28 13:05 (Lima) · main · Arranque del repositorio

- **Quién**: Claude Code, a pedido de Jefferson («Implementa la branch develop … quiero que apliques la misma configuración para tener un correcto versionado»). Configuración copiada de `IQBF-ULIMA_Back` y `IQBF-ULIMA_Front`, leída con `gh api` (protección de `main` y `develop`, `ci.yml`, `release.yml` y `docs/devops.md`).
- **Qué cambió**: primer commit en `main` con `README.md`, `AGENTS.md`, `CLAUDE.md`, `MEMORIA.md`, `CHANGELOG.md`, `VERSION`, `.gitignore`, `docs/devops.md`, `.github/workflows/ci.yml` (checks `pruebas` y `flujo`), `.github/workflows/release.yml`, la plantilla de PR, `scripts/preflight.sh`, `scripts/probar_preflight.sh` y `scripts/hooks/pre-commit`. Después se crea `develop` desde `main`, queda como rama por defecto, y se protegen las dos ramas como en IQBF (`main` con `pruebas` y `flujo`, `develop` con `pruebas`, PR obligatorio, sin empujes forzados ni borrado).
- **Por qué**: versionado con `develop` y `main` como en IQBF, y memoria de cada cambio para que un agente retome el trabajo con certeza (pedido de Jefferson del 28/10/2026).
- **Lo que debe hacer, cómo se probó**: `bash scripts/probar_preflight.sh` da «15 bien, 0 mal». Pasan el commit y el PR con `MEMORIA.md`, el xlsx y el csv inventados con códigos 99 dentro de `tests/datos_inventados/`, `.env.example` sin valores, la referencia `${{ secrets.X }}` y el repositorio limpio.
- **Lo que no debe hacer, cómo se probó**: en la misma corrida fallan, como se espera, el commit y el PR sin `MEMORIA.md`, un xlsx fuera de `tests/datos_inventados/`, un xlsx y un csv con un código que no empieza con 99, un `.env` versionado, una cadena de conexión con clave y un token con valor, y ninguno de esos mensajes muestra el secreto falso.
- **Correcciones**: en la primera corrida dos casos pasaban sin probar nada, porque la limpieza entre casos borraba la carpeta vacía de datos inventados. El arnés vuelve a crearla en cada caso. La primera versión de la regla 2 se saltaba un código de cada dos cuando venían separados por una sola coma, y ahora toma cada número completo. Antes del commit, la revisión previa marcó como secretos los secretos falsos del propio arnés, lo que confirma la regla 4; `scripts/probar_preflight.sh` queda fuera del escaneo de secretos con un comentario que lo explica.
- **Cómo se reporta**: este registro, `CHANGELOG.md` («Sin publicar») y el check `pruebas` de cada PR.
- **Pendiente y siguiente paso**: comprobar en GitHub la rama por defecto y la protección; abrir el PR del plan del MVP a `develop`; agregar SonarQube Cloud y Snyk cuando existan los tokens.
