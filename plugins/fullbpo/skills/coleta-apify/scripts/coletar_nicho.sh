#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# coletar_nicho.sh — coleta VÁRIOS perfis de um nicho (base das frentes
# mapa-nicho e playbook-virais). Roda o coleta-apify perfil para cada handle
# e deixa uma pasta nicho_<slug>/ com um perfil_analise por creator.
#
# Uso:
#   APIFY_TOKEN=... coletar_nicho.sh <slug> <@h1> <@h2> ... [--nicho "termo"] [--n N]
#
# Idempotente: pula perfis já coletados. Saída: nicho_<slug>/<handle>.json
# (+ produtos.json se --nicho). Imprime a pasta no final.
# ---------------------------------------------------------------------------
set -uo pipefail
SLUG="${1:-}"; shift || true
[[ -z "$SLUG" ]] && { echo "uso: coletar_nicho.sh <slug> <@h1> <@h2> ... [--nicho termo] [--n N]" >&2; exit 2; }

HANDLES=(); NICHO=""; N=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --nicho) NICHO="$2"; shift 2;;
    --n) N="$2"; shift 2;;
    *) HANDLES+=("$1"); shift;;
  esac
done
[[ ${#HANDLES[@]} -eq 0 ]] && { echo "ERRO: informe ao menos 1 handle." >&2; exit 2; }

HERE="$(cd "$(dirname "$0")" && pwd)"        # .../coleta-apify/scripts
APIFY="$HERE/apify.py"
OUT="nicho_${SLUG}"
mkdir -p "$OUT"
log(){ echo ">> $*" >&2; }

for h in "${HANDLES[@]}"; do
  H="${h#@}"
  dest="$OUT/${H}.json"
  if [[ -s "$dest" ]]; then log "$H já coletado — pulando"; continue; fi
  log "Coletando @$H..."
  python3 "$APIFY" perfil "@$H" "$dest" ${N:+--n "$N"} || log "aviso: falha em @$H (segue)"
done

if [[ -n "$NICHO" && ! -s "$OUT/produtos.json" ]]; then
  log "Coletando produtos do nicho: $NICHO..."
  python3 "$APIFY" produtos "$NICHO" "$OUT/produtos.json" ${N:+--n "$N"} || log "aviso: produtos falhou"
fi

echo ""
echo "nicho pronto: $OUT"
ls -1 "$OUT"
