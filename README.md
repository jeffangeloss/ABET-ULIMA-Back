# ABET-ULIMA-Back

Backend del sistema de medición ABET de la Carrera de Ingeniería Ambiental de la Universidad de Lima. Recibe el export de Blackboard de una sección, lo valida, guarda sus datos en PostgreSQL 18 (Neon, us-east-1) en una sola transacción y genera el Excel del R-17 con la constancia de la carga, que el profesor conserva como evidencia.

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

## Demo del corte 1

La demo corre en la Mac, sin Neon, con PostgreSQL 18 y uv instalados.

```bash
bash scripts/demo_corte1.sh                      # salida en ${TMPDIR:-/tmp}/abet_demo_corte1
bash scripts/demo_corte1.sh /ruta/de/salida      # salida en otra carpeta
bash scripts/demo_corte1.sh --conservar          # deja el clúster arriba y dice cómo conectarse y apagarlo
```

El guion arma con `db/pruebas/cluster_desechable.sh` un clúster desechable con su socket propio, así que nunca toca el clúster de la Mac. En él crea una base con las migraciones, las vistas del R-17, la guardia de datos inventados, el rol de la aplicación y los datos inventados de 2026-2. Con `SET ROLE` a ese rol, el comando `python -m abet_carga` muestra lo siguiente.

- `docente410@example.invalid` carga `export_inventado_410_con_error.xlsx` en la 410 de 450002 y ve 11 filas leídas, 10 aceptadas y 1 rechazada (fila 3, PI 5.2, `NIVEL_FUERA_DE_ESCALA`), con la huella SHA-256 (Secure Hash Algorithm de 256 bits) del archivo y sin ningún nombre ni valor leído.
- La segunda carga del mismo archivo responde `YA_PUBLICADA` con la misma carga y no agrega filas.
- El R-17 `R017_450002_410_2026-2_PROVISIONAL.xlsx` y `constancia_<carga>.json` quedan en la carpeta de salida, con 60,0 %, 60,0 % y 70,0 % en 5.1, 5.2 y 5.3, y las consultas de control Q01 a Q14 dan 0 filas.
- Con `db/datos/varias_secciones_2026_2_inventado.sql`, `docente.varias@example.invalid` ve rechazados el export de la 410 de 450010 en su 412 y el de la 412 de 450010 en la 412 de 450002, publica cada export en su sección y recibe «La sección no está a su cargo.» en la 410 de 450002.

El guion sale con 0 solo si ve esas cifras. El comando también sirve solo, con `--base` o `DATABASE_URL` y `CONJUNTO_REGLAS` en el entorno, y `python -m abet_carga --help` lista sus subcomandos `cargar` y `r17`.

Lo que todavía no existe en el corte 1 es la interfaz de programación de aplicaciones (application programming interface, API) de FastAPI (T036 a T038), las pantallas del Front y la base en Neon.
