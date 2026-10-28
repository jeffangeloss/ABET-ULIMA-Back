# ABET-ULIMA-Back

Backend del sistema de medición ABET de la Carrera de Ingeniería Ambiental de la Universidad de Lima. Recibe el export de Blackboard de una sección, lo valida, guarda sus datos en PostgreSQL 16 (Neon, São Paulo) en una sola transacción y genera el Excel del R-17 con la constancia de la carga, que el profesor conserva como evidencia.

**Estado al 28/10/2026.** Jefferson aprueba el plan del MVP (spec 001) y el corte 1 avanza en la rama `feat/001-mvp-carga-r17`, todavía en local. La base de datos ya está en `db/`, traída con su historia desde el repositorio privado `jeffangeloss/ABET_ULIMA`, y el esqueleto de Python corre sus pruebas con uv. La carga del export y el R-17 todavía no existen.

## Antes de trabajar

1. Leer `MEMORIA.md`, que dice dónde quedó el trabajo, y `AGENTS.md`, que fija las reglas para personas y agentes.
2. Activar la revisión local una vez por clon con `git config core.hooksPath scripts/hooks`.
3. Revisar `docs/devops.md` para las ramas, las versiones y los entornos.

## Reglas que no cambian

- Solo datos inventados (códigos de estudiante que empiezan con 99) en el repositorio, en Neon y en Vercel, hasta que la universidad autorice los reales.
- Ningún nombre de estudiante se guarda ni se muestra.
- Ninguna credencial entra al repositorio ni a los registros.
- Todo cambio entra por PR a `develop` y actualiza `MEMORIA.md`.
