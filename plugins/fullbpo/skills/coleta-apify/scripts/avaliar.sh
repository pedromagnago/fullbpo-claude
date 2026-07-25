#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# avaliar.sh — orquestra uma avaliação completa de um creator:
#   perfil (Apify) [+ vídeo de referência] [+ produtos do nicho] -> dossiê
#   com os JSONs normalizados e um conteudo.json pré-preenchido.
#
# Uso:
#   APIFY_TOKEN=... avaliar.sh <@handle> [--video URL] [--nicho "termo"] \
#                              [--saida DIR] [--n N]
#
# Idempotente: pula etapas cujo resultado já existe (use --forcar para refazer).
# Depois, o analista/Claude preenche os TODO do conteudo.json e roda os
# renderizadores (estudo-de-video / painel-vendas).
# ---------------------------------------------------------------------------
set -uo pipefail

HANDLE="" ; VIDEO="" ; NICHO="" ; OUT="" ; N="" ; FORCAR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --video) VIDEO="$2"; shift 2;;
    --nicho) NICHO="$2"; shift 2;;
    --saida) OUT="$2"; shift 2;;
    --n) N="$2"; shift 2;;
    --forcar) FORCAR=1; shift;;
    *) [[ -z "$HANDLE" ]] && HANDLE="$1"; shift;;
  esac
done
[[ -z "$HANDLE" ]] && { echo "uso: avaliar.sh <@handle> [--video URL] [--nicho termo] [--saida DIR] [--n N]" >&2; exit 2; }

H="${HANDLE#@}"                                   # tira @
SKILLS="$(cd "$(dirname "$0")/../.." && pwd)"     # .../plugins/fullbpo/skills
APIFY="$SKILLS/coleta-apify/scripts/apify.py"
ESQ="$SKILLS/coleta-apify/scripts/montar_esqueleto.py"
ASSISTIR="$SKILLS/assistir-video/scripts/assistir_video.sh"
WORK="${OUT:-avaliacao_${H}_$(date +%Y%m%d)}"
mkdir -p "$WORK"
log(){ echo ">> $*" >&2; }

# 1. Perfil (Apify)
if [[ -n "$FORCAR" || ! -s "$WORK/perfil_analise.json" ]]; then
  log "Coletando perfil @$H..."
  python3 "$APIFY" perfil "@$H" "$WORK/perfil_analise.json" ${N:+--n "$N"} || { echo "ERRO na coleta de perfil" >&2; exit 3; }
else log "perfil_analise.json já existe — pulando (use --forcar)"; fi

# 2. Produtos do nicho (opcional)
if [[ -n "$NICHO" ]]; then
  if [[ -n "$FORCAR" || ! -s "$WORK/produtos.json" ]]; then
    log "Coletando produtos do nicho: $NICHO..."
    python3 "$APIFY" produtos "$NICHO" "$WORK/produtos.json" ${N:+--n "$N"} || log "aviso: coleta de produtos falhou (segue sem)"
  else log "produtos.json já existe — pulando"; fi
fi

# 3. Vídeo de referência (opcional)
if [[ -n "$VIDEO" ]]; then
  if [[ -n "$FORCAR" || ! -d "$WORK/video/frames" ]]; then
    log "Analisando vídeo de referência..."
    bash "$ASSISTIR" "$VIDEO" "$WORK/video" || log "aviso: análise de vídeo falhou (segue sem)"
  else log "vídeo já coletado — pulando"; fi
fi

# 4. Esqueleto do conteudo.json (dados reais + TODO qualitativo)
python3 "$ESQ" "$WORK/perfil_analise.json" "$WORK"

# 5. LEIA-ME com os próximos passos
cat > "$WORK/LEIA-ME.txt" <<EOF
DOSSIÊ DE AVALIAÇÃO — @$H
Gerado por avaliar.sh (FullBPO).

Arquivos:
  perfil_analise.json   métricas do perfil (Apify)
$( [[ -s "$WORK/produtos.json" ]] && echo "  produtos.json         produtos do nicho (Radar)" )
$( [[ -d "$WORK/video/frames" ]] && echo "  video/                transcrição + frames do vídeo de referência" )
  conteudo.json         esqueleto do relatório (PREENCHER os campos TODO)

Próximos passos (analista/Claude):
  1. Preencher os TODO em conteudo.json (resumo, leitura do perfil, insights$( [[ -d "$WORK/video/frames" ]] && echo ", linha do tempo do vídeo" )).
  2. Gerar o RELATÓRIO:
     python3 "$SKILLS/estudo-de-video/scripts/montar_relatorio.py" "$WORK/conteudo.json" "$WORK/relatorio.html"
$( [[ -s "$WORK/produtos.json" ]] && echo "  3. RADAR de produtos: usar produtos.json (ranking de virais do nicho)." )
  *  PAINEL de vendas EXATO do cliente: alimentar vendas.json com o export do
     Affiliate Center e rodar painel-vendas/scripts/montar_painel.py.
EOF

echo ""
echo "===== AVALIAÇÃO PRONTA ====="
echo "dossiê: $WORK"
ls -1 "$WORK"
echo "próximos passos: $WORK/LEIA-ME.txt"
echo "==========================="
