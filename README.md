# ABET-ULIMA-Back

Backend del sistema de medición ABET de la Carrera de Ingeniería Ambiental de la Universidad de Lima. Recibe el export de Blackboard de una sección, lo valida, guarda sus datos en PostgreSQL 16 (Neon, São Paulo) en una sola transacción y genera el Excel del R-17 con la constancia de la carga, que el profesor conserva como evidencia.

**Estado al 28/10/2026.** El repositorio está en arranque. El plan del MVP está en revisión y todavía no hay código de producto. La base de datos vive por ahora en el repositorio privado `jeffangeloss/ABET_ULIMA` y pasa a la carpeta `db/` de este repositorio cuando termine su despliegue en Neon.

## Antes de trabajar

1. Leer `MEMORIA.md`, que dice dónde quedó el trabajo, y `AGENTS.md`, que fija las reglas para personas y agentes.
2. Activar la revisión local una vez por clon con `git config core.hooksPath scripts/hooks`.
3. Revisar `docs/devops.md` para las ramas, las versiones y los entornos.

## Reglas que no cambian

- Solo datos inventados (códigos de estudiante que empiezan con 99) en el repositorio, en Neon y en Vercel, hasta que la universidad autorice los reales.
- Ningún nombre de estudiante se guarda ni se muestra.
- Ninguna credencial entra al repositorio ni a los registros.
- Todo cambio entra por PR a `develop` y actualiza `MEMORIA.md`.
