#!/usr/bin/env bash
# Hook Stop de Claude Code (.claude/settings.json). Si el turno termina con cambios sin commit y
# MEMORIA.md no está entre ellos, devuelve el control a Claude con la instrucción de actualizar la
# memoria (AGENTS.md, regla 2). No bloquea dos veces seguidas, para no entrar en bucle.
entrada="$(cat)"
if printf '%s' "$entrada" | grep -Eq '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then
  exit 0
fi
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0
git rev-parse --is-inside-work-tree > /dev/null 2>&1 || exit 0
cambios="$(git status --porcelain --untracked-files=all 2>/dev/null | awk '{print $NF}')"
[ -z "$cambios" ] && exit 0
if printf '%s\n' "$cambios" | grep -qx 'MEMORIA.md'; then
  exit 0
fi
echo "Hay cambios sin commit y MEMORIA.md no los registra. Antes de terminar, actualiza «Punto actual» y agrega una entrada al «Registro» con lo que cambió, por qué, cómo se probó lo que debe hacer y lo que no debe hacer, las correcciones y cómo se reporta (AGENTS.md, regla 2)." >&2
exit 2
