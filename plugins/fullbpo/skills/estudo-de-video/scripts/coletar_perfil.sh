#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# coletar_perfil.sh — coleta métricas públicas de um perfil (TikTok, etc.)
# e calcula uma análise agregada para o relatório de estudo.
#
# Uso:
#   coletar_perfil.sh <URL_do_perfil> [pasta_saida] [qtd_videos]
#
# Saída: <pasta_saida>/perfil_analise.json (métricas + top vídeos + hashtags)
# e imprime um resumo legível. Usa o backend padrão do yt-dlp (respeita
# HTTPS_PROXY; NÃO instalar curl_cffi — impersonation TLS é resetada por proxy).
# ---------------------------------------------------------------------------
set -uo pipefail
URL="${1:-}"
OUTDIR="${2:-$(mktemp -d 2>/dev/null || echo /tmp/perfil-$$)}"
QTD="${3:-24}"
[[ -z "$URL" ]] && { echo "ERRO: informe a URL do perfil." >&2; exit 2; }
mkdir -p "$OUTDIR"; cd "$OUTDIR" || exit 2

python3 -c "import yt_dlp" 2>/dev/null || pip install -q yt-dlp >&2

echo ">> Coletando lista de vídeos do perfil (recentes: $QTD)..." >&2
python3 -m yt_dlp --flat-playlist --playlist-end "$QTD" -J "$URL" > profile.json 2>/dev/null \
  || { echo "ERRO: não consegui coletar o perfil (privado, bloqueado ou URL inválida)." >&2; exit 3; }

python3 - "$OUTDIR" <<'PY'
import json, re, sys, statistics as st
from datetime import datetime, timezone
outdir = sys.argv[1]
d = json.load(open("profile.json"))
ents = [e for e in (d.get("entries") or []) if e.get("view_count") is not None]
if not ents:
    print("ERRO: perfil sem vídeos com métricas públicas.", file=sys.stderr); sys.exit(3)
num = lambda e,k: e.get(k) or 0
views=[num(e,'view_count') for e in ents]; likes=[num(e,'like_count') for e in ents]
coms=[num(e,'comment_count') for e in ents]; shares=[num(e,'repost_count') for e in ents]
saves=[num(e,'save_count') for e in ents]; durs=[num(e,'duration') for e in ents]
ts=[e['timestamp'] for e in ents if e.get('timestamp')]
dmin,dmax=(min(ts),max(ts)) if ts else (0,0)
days=max(1,(dmax-dmin)/86400) if ts else 1
er=lambda e:(num(e,'like_count')+num(e,'comment_count')+num(e,'repost_count')+num(e,'save_count'))/(num(e,'view_count') or 1)
tags={}
for e in ents:
    for t in re.findall(r"#\w+",(e.get('description') or '')+' '+(e.get('title') or '')):
        tags[t.lower()]=tags.get(t.lower(),0)+1
top_tags=sorted(tags.items(),key=lambda x:-x[1])[:12]
top=sorted(ents,key=lambda e:-num(e,'view_count'))[:5]
fdate=lambda t: datetime.fromtimestamp(t,tz=timezone.utc).strftime("%d/%m/%Y")
br=lambda n: f"{int(n):,}".replace(",",".")
out={
 "handle": d.get("title") or "",
 "amostra": len(ents),
 "periodo": [fdate(dmin),fdate(dmax)] if ts else ["",""],
 "dias": round(days),
 "cadencia_semana": round(len(ents)/days*7,1),
 "views": {"media":int(st.mean(views)),"mediana":int(st.median(views)),"min":min(views),"max":max(views)},
 "likes_media": int(st.mean(likes)), "coment_media": int(st.mean(coms)),
 "shares_media": int(st.mean(shares)), "saves_media": int(st.mean(saves)),
 "engajamento_proxy": round(st.mean([er(e) for e in ents])*100,1),
 "duracao_media": round(st.mean(durs)),
 "top_hashtags": top_tags,
 "top_videos": [{"views":num(e,'view_count'),"likes":num(e,'like_count'),
                 "data":fdate(e['timestamp']) if e.get('timestamp') else "",
                 "titulo":(e.get('title') or '')[:70],"url":e.get('url')} for e in top],
}
json.dump(out, open(f"{outdir}/perfil_analise.json","w"), ensure_ascii=False, indent=2)
print(f">> @{out['handle']}: {out['amostra']} vídeos | {out['cadencia_semana']}/sem | "
      f"views méd {br(out['views']['media'])} | engaj {out['engajamento_proxy']}% | "
      f"dur méd {out['duracao_media']}s", file=sys.stderr)
print(f">> perfil_analise.json salvo em {outdir}", file=sys.stderr)
PY
echo "$OUTDIR/perfil_analise.json"
