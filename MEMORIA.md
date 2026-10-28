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
- **Rama de trabajo**: `docs/plan-mvp`, en PR a `develop` (después de `chore/seguridad-y-memoria`, PR #1)
- **Versión publicada**: ninguna (`VERSION` = 0.0.0)
- **Último cambio**: spec 001 del MVP con historias auditadas, `.feature`, plan, tareas y constitución
- **En curso**: aprobación de la spec `specs/001-mvp-carga-r17/` por Jefferson (merge de este PR o su «apruebo» explícito)
- **Siguiente paso**: con la spec aprobada, fase 1 (contrato y specs vivas) y fase 2 (base en Neon, traslado de `bd/` y V1_09), en `feat/001-mvp-carga-r17`
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

### 2026-10-28 16:55 (Lima) · docs/plan-mvp · Spec 001 del MVP con historias auditadas

- **Quién**: Claude Code, con flujos de agentes. Tres escritores redactaron 29 historias desde los ángulos del profesor, del coordinador con la base y de la evidencia con la privacidad, y quedaron 25 candidatas al unirlas. Tres auditores trataron de refutarlas (necesidad, solapamiento y tamaño, verificabilidad contra la base) y un crítico atacó las decisiones técnicas. Después, cinco redactores escribieron la spec, los `.feature`, el plan y las tareas con el esquema de IQBF; cuatro revisores (constructor, consistencia, hechos y estilo) hallaron 99 problemas, y tres vueltas de corrección con verificador los cerraron.
- **Qué cambió**: `.specify/memory/constitution.md` (seis principios, versión 1.0.0 sin ratificar), `specs/README.md`, `specs/001-mvp-carga-r17/spec.md` (21 historias US-01 a US-21, FR, SC, decisiones D-01 a D-13 y J-01 a J-09), `revision-historias.md` (veredictos de la auditoría por candidata C-01 a C-25), `aceptacion/*.feature` (seis archivos, 127 escenarios en Gherkin en español), `plan.md` (fases 0 a 7 y cortes) y `tasks.md`.
- **Por qué**: pedido de Jefferson del 28/10/2026, «Dime el plan que implementaremos», con el objetivo del sprint en sus palabras (base en la nube, subir el export, generar el R-17 y cargar los datos) y el método de historias auditadas.
- **Lo que debe hacer, cómo se probó**: el revisor de hechos recalculó contra `bd/pruebas/datos_sinteticos.sql` las cifras de los escenarios (63,6 / 63,6 / 72,7 con 11 estudiantes; 60,0 / 60,0 / 70,0 con la fila 3 rechazada; 90,9 % con las reglas aprobadas de prueba) y cotejó cada nombre con las migraciones; el verificador final confirma que IDs, títulos, cortes, rutas, mensajes y archivos coinciden entre la spec, los `.feature`, el plan y las tareas. `bash scripts/preflight.sh --staged` sin fallas.
- **Lo que no debe hacer, cómo se probó**: los únicos códigos fuera del rango 99 son los valores de prueba de la guardia (10000004 y 98999999) dentro de `specs/`; los correos son `@example.invalid`; no hay credenciales (barridos con grep de los revisores).
- **Correcciones**: la spec citaba 20 archivos `.feature` que no existían, los `.feature` tenían dos ubicaciones, las candidatas compartían numeración con las historias finales, el export sin sección declarada tenía tres comportamientos y la constitución nombraba una columna inexistente (`nombre` en lugar de `nombre_archivo`); todo quedó corregido. Quedan cuatro diferencias menores entre la spec y los `.feature`: escenarios de US-07 a US-14 que nombran P3 o P4, US-01 escenario 1 sin `abet.so` ni `abet.instrumento`, US-08 escenario 3 que promete el registro de la aplicación y SC-006, que cita los registros de Vercel.
- **Cómo se reporta**: PR de `docs/plan-mvp` a `develop`; su merge es la aprobación de la spec.
- **Pendiente y siguiente paso**: las decisiones D y J de la spec; crear el proyecto de Neon (Jefferson); fusionar `preparacion-neon` antes de trasladar `bd/`.

### 2026-10-28 14:55 (Lima) · chore/seguridad-y-memoria · Descarga de gitleaks solo por HTTPS

- **Quién**: Claude Code, tras el hallazgo de SonarQube Cloud en el PR #1 del Back («Not enforcing HTTPS here might allow for redirections to insecure websites», `.github/workflows/ci.yml:50`), que dejó la puerta de calidad en «C Security Rating on New Code».
- **Qué cambió**: el `curl` del job `secretos` lleva `--proto '=https' --tlsv1.2`, de modo que una redirección no puede llevar la descarga a HTTP. Corrige la entrada «Hook de memoria, secretos, SonarQube Cloud y Snyk» de esta misma fecha.
- **Por qué**: la suma SHA-256 ya detectaba un archivo alterado, pero la regla de SonarQube Cloud pide además que la descarga no salga de HTTPS.
- **Lo que debe hacer, cómo se probó**: la nueva corrida del PR debe dejar la puerta de calidad de SonarQube Cloud en verde y el job `secretos` en verde.
- **Lo que no debe hacer, cómo se probó**: con `--proto '=https'`, curl rechaza seguir una redirección a una dirección http.
- **Correcciones**: esta entrada corrige la anterior; la anterior no se edita.
- **Cómo se reporta**: el check de SonarQube Cloud y el job `secretos` del PR.
- **Pendiente y siguiente paso**: ninguno nuevo.

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
