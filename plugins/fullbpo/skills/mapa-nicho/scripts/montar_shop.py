#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# montar_shop.py — Frente 1 (Shop): dash estratégico CENTRADO EM 1 CREATOR.
# Responde, para o creator-alvo (ex.: a cliente Priscila): onde ela está,
# COMO A CONCORRÊNCIA VIRALIZA, QUAIS VÍDEOS VIRALIZAM no nicho e QUAIS
# PRODUTOS vendem bem e ela pode adotar — com recomendações.
#
# Uso: montar_shop.py <shop.json> [saida.html] [--perfis <dir>]
#   --perfis <dir>  pasta com <handle>.json (do coletar_nicho.sh). Quando dada,
#                   embute UM DOSSIÊ por perfil avaliado (KPIs + vídeos de maior
#                   alcance + ângulo/hashtags + "segredo da trend") e transforma
#                   os @handles das tabelas em links (âncora) para o dossiê.
#
# Produtos: preços são normalizados para BRL. Se o produto vier em USD, use o
# câmbio de referência (campo "cambio" no shop.json; padrão 5.08) — o dash
# mostra "R$ x (US$ y)". O nome do produto vira link se houver "url".
#
# Esquema do shop.json: ver SKILL.md (mapa-nicho).
# ---------------------------------------------------------------------------
import sys, os, json, html

CAMBIO_PADRAO = 5.08  # USD->BRL de referência (ajustável via campo "cambio")

def esc(s): return html.escape(str(s if s is not None else ""), quote=True)
def bi(n):
    try: return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError): return "—"
def brl(v):
    try: v=float(v)
    except (TypeError, ValueError): return "—"
    s=f"{v:,.2f}".replace(",","§").replace(".",",").replace("§",".")
    return f"R$ {s}"
def num_pt(v):
    try: return str(v).replace(".",",")
    except (TypeError, ValueError): return "—"
def rich(s):
    s = esc(s); out=[]; b=False
    for seg in s.split("**"):
        p=[]; i=False
        for sub in seg.split("*"): p.append(f"<em>{sub}</em>" if i else sub); i=not i
        seg="".join(p); out.append(f"<strong>{seg}</strong>" if b else seg); b=not b
    return "".join(out)
def paras(v):
    if not v: return ""
    if isinstance(v,str): v=[v]
    return "".join(f"<p>{rich(p)}</p>" for p in v)

def preco_cell(p, cambio):
    """Célula de preço em BRL. Se USD, converte e mostra o original em cinza."""
    preco=p.get("preco"); moeda=(p.get("moeda") or "").upper()
    pbrl=p.get("preco_brl")
    if pbrl is None and moeda=="USD" and cambio and preco is not None:
        try: pbrl=float(preco)*float(cambio)
        except (TypeError, ValueError): pbrl=None
    if pbrl is None and moeda in ("BRL","R$","REAL") and preco is not None:
        try: pbrl=float(preco)
        except (TypeError, ValueError): pbrl=None
    if pbrl is None:
        return f'{esc(preco)} {esc(p.get("moeda"))}'
    orig=""
    if moeda=="USD" and preco is not None:
        try: usd=f"{float(preco):,.2f}".replace(",","§").replace(".",",").replace("§",".")
        except (TypeError, ValueError): usd=num_pt(preco)
        orig=f'<span class=orig>US$ {usd}</span>'
    return f'{brl(pbrl)}{orig}'

def parse_args(argv):
    perfis_dir=None
    a=list(argv[1:])
    if "--perfis" in a:
        i=a.index("--perfis")
        perfis_dir=a[i+1] if i+1<len(a) else None
        del a[i:i+2]
    if not a:
        print("uso: montar_shop.py <shop.json> [saida.html] [--perfis <dir>]",file=sys.stderr); sys.exit(2)
    shop=a[0]; saida=a[1] if len(a)>1 else "shop.html"
    return shop, saida, perfis_dir

def carregar_perfil(perfis_dir, handle):
    if not perfis_dir or not handle: return None
    p=os.path.join(perfis_dir, f"{handle}.json")
    if not os.path.exists(p): return None
    try: return json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError): return None

def video_li(v):
    t=esc(v.get("titulo")); url=v.get("url")
    tt=f'<a href="{esc(url)}" target="_blank" rel="noopener">{t} ↗</a>' if url else t
    stats=f'{bi(v.get("views"))} views · {bi(v.get("likes"))} likes'
    if v.get("data"): stats+=f' · {esc(v.get("data"))}'
    return f'<li><div class=tv-t>{tt}</div><div class=tv-s>{stats}</div></li>'

def dossie_section(handle, perfil, meta):
    """Uma 'página de análise' por perfil, embutida (âncora #d-handle)."""
    nome=meta.get("nome") or perfil.get("nome") or handle
    alvo=meta.get("alvo")
    views=perfil.get("views",{}) or {}
    kp=[("Seguidores",bi(perfil.get("seguidores"))),
        ("Views (mediana)",bi(views.get("mediana"))),
        ("Melhor vídeo",bi(views.get("max"))),
        ("Engajamento",f'{num_pt(perfil.get("engajamento_proxy"))}%'),
        ("Cadência",f'{num_pt(perfil.get("cadencia_semana"))}/sem'),
        ("Duração méd",f'{perfil.get("duracao_media")}s')]
    ktiles="".join(f'<div class=kpi><div class=k-v>{v}</div><div class=k-k>{esc(l)}</div></div>'
                   for l,v in kp)
    tops="".join(video_li(v) for v in perfil.get("top_videos",[]))
    chips="".join(
        f'<span class=chip>{esc(t[0] if isinstance(t,(list,tuple)) else t)}'
        f'{f"<span class=chip-n>{esc(t[1])}</span>" if isinstance(t,(list,tuple)) and len(t)>1 else ""}</span>'
        for t in (perfil.get("top_hashtags") or [])[:12])
    leitura=meta.get("leitura")
    seg=meta.get("segredo")
    if not seg and perfil.get("top_videos"):
        tv=perfil["top_videos"][0]
        seg=(f'O maior alcance dela veio de **“{esc((tv.get("titulo") or "")[:70]).strip()}…”** '
             f'({bi(tv.get("views"))} views). Esse é o gancho/formato a **estudar e adaptar**.')
    perfil_url=perfil.get("perfil_url") or f'https://www.tiktok.com/@{handle}'
    bio=perfil.get("bio")
    return f"""
<section class="sec dossie" id="d-{esc(handle)}">
  <span class="eyebrow">Avaliação {"· ALVO" if alvo else "· referência"}</span>
  <h2>@{esc(handle)} <span class=dsub>{esc(nome)}</span></h2>
  {f'<div class=bio>{esc(bio)}</div>' if bio else ''}
  {f'<div class=lead>{paras(leitura)}</div>' if leitura else ''}
  <div class=kpis>{ktiles}</div>
  {f'<div class="callout"><span class=tag>Segredo da trend</span> {rich(seg)}</div>' if seg else ''}
  <div class=two>
    <div class=card><h3>Dossiê — vídeos de maior alcance</h3>
      {f'<ol class=tops>{tops}</ol>' if tops else '<p class=note>Sem amostra de vídeos.</p>'}</div>
    <div class=card><h3>Ângulo &amp; hashtags</h3>
      {f'<div class=chips>{chips}</div>' if chips else '<p class=note>Sem hashtags recorrentes.</p>'}
      <p class=note><a href="{esc(perfil_url)}" target="_blank" rel="noopener">Abrir perfil no TikTok ↗</a></p></div>
  </div>
  <p class=back><a href="#mapa">↑ Voltar ao mapa competitivo</a></p>
</section>"""

def main():
    shop_json, saida, perfis_dir = parse_args(sys.argv)
    d=json.load(open(shop_json,encoding="utf-8"))
    s=d.get("subject",{})
    cambio=d.get("cambio", CAMBIO_PADRAO)

    # --- perfis p/ dossiê + mapa handle->meta (nome/leitura/segredo/alvo) ---
    ordem=[]; perfis={}; meta={}
    if s.get("handle"):
        h=s["handle"]; ordem.append(h)
        dd=s.get("dossie",{}) or {}
        meta[h]={"nome":s.get("nome"),"alvo":True,
                 "leitura":dd.get("leitura"),"segredo":dd.get("segredo")}
    for c in d.get("concorrentes",[]):
        h=c.get("handle")
        if not h: continue
        ordem.append(h)
        dd=c.get("dossie",{}) or {}
        meta[h]={"nome":c.get("nome"),"alvo":False,
                 "leitura":dd.get("leitura") or c.get("como_viraliza"),
                 "segredo":dd.get("segredo")}
    for h in ordem:
        pf=carregar_perfil(perfis_dir,h)
        if pf: perfis[h]=pf
    dossies=set(perfis.keys())

    def hlink(h):
        return f'<a href="#d-{esc(h)}">@{esc(h)}</a>' if h in dossies else f'@{esc(h)}'

    # bloco 0 — KPIs do alvo
    kpis=[("Seguidores",bi(s.get("seguidores")),""),
          ("Views (mediana)",bi(s.get("mediana")),"alcance típico"),
          ("Melhor vídeo",bi(s.get("melhor")),"o teto dela"),
          ("Engajamento",f'{num_pt(s.get("engajamento"))}%',""),
          ("Cadência",f'{num_pt(s.get("cadencia"))}/sem',""),
          ("Duração méd",f'{s.get("duracao")}s',"")]
    ktiles="".join(f'<div class=kpi><div class=k-v>{v}</div><div class=k-k>{esc(l)}</div>'
                   f'{f"<div class=k-n>{esc(n)}</div>" if n else ""}</div>' for l,v,n in kpis)
    viral=s.get("viral") or {}
    viral_html=(f'<div class="callout"><span class=tag>Prova de que dá</span>'
                f'<b>Ela já viralizou:</b> <a href="{esc(viral.get("url"))}" target="_blank" rel="noopener">{esc(viral.get("titulo"))}</a> — '
                f'<b>{bi(viral.get("views"))} views</b> ({esc(viral.get("multiplo"))}× a mediana).</div>') if viral else ""

    # bloco 1 — concorrência lado a lado (alvo + concorrentes)
    def linha(p,alvo=False):
        cls=' class="alvo"' if alvo else ''
        h=p.get("handle")
        return (f'<tr{cls}><td class=who><b>{hlink(h)}</b>'
                f'<span class=nome>{esc(p.get("nome") or "")}{" · ALVO" if alvo else ""}</span></td>'
                f'<td class=num>{bi(p.get("seguidores"))}</td><td class=num>{bi(p.get("mediana"))}</td>'
                f'<td class=num>{num_pt(p.get("engajamento"))}%</td>'
                f'<td class=num>{bi(p.get("melhor"))}</td></tr>')
    rows=linha(s,alvo=True)+"".join(linha(c) for c in d.get("concorrentes",[]))
    comoviral="".join(
        f'<div class=card><b>{hlink(c.get("handle"))}</b><p>{rich(c.get("como_viraliza"))}</p></div>'
        for c in d.get("concorrentes",[]) if c.get("como_viraliza"))

    # bloco 2 — vídeos virais do nicho
    vrows="".join(
        f'<tr><td class=num><b>{esc(v.get("multiplo"))}×</b></td><td class=num>{bi(v.get("views"))}</td>'
        f'<td>{hlink(v.get("handle"))}</td>'
        f'<td><a href="{esc(v.get("url"))}" target="_blank" rel="noopener">{esc(v.get("titulo"))} ↗</a></td></tr>'
        for v in d.get("virais_nicho",[]))

    # bloco 3 — produtos do nicho (BRL + link)
    prows=""
    for p in d.get("produtos_nicho",[]):
        nome=esc(p.get("produto")); url=p.get("url")
        nome_html=f'<a href="{esc(url)}" target="_blank" rel="noopener">{nome} ↗</a>' if url else nome
        rating=p.get("rating")
        rat=f'<div class=star>★ {num_pt(rating)}</div>' if rating else ""
        prows+=(f'<tr><td class=prod>{nome_html}{rat}</td><td class=num><b>{bi(p.get("vendas"))}</b></td>'
                f'<td class=num>{preco_cell(p,cambio)}</td><td>{esc(p.get("loja"))}</td></tr>')

    # bloco 4 — recomendações
    recs=""
    for i,r in enumerate(d.get("recomendacoes",[]),1):
        recs+=f'<div class=rec><span class=r-n>{i:02d}</span><h3>{rich(r.get("titulo"))}</h3>{paras(r.get("texto"))}</div>'

    # bloco 5 — avaliações (índice) + dossiês embutidos
    aval_html=""; dossies_html=""
    if perfis:
        cards=""
        for h in ordem:
            if h not in perfis: continue
            m=meta.get(h,{}); pf=perfis[h]
            nome=m.get("nome") or pf.get("nome") or h
            segue=bi(pf.get("seguidores"))
            tag='<span class=aval-tag>ALVO</span>' if m.get("alvo") else ''
            cards+=(f'<a class=aval-card href="#d-{esc(h)}"><b>@{esc(h)} {tag}</b>'
                    f'<span class=aval-nome>{esc(nome)} · {segue} seg.</span>'
                    f'<span class=go>Ver análise completa →</span></a>')
        aval_html=(f'<section class=sec><span class=eyebrow>Avaliações · dossiê por perfil</span>'
                   f'<h2>Análise de cada perfil avaliado</h2>'
                   f'<p class=note>Clique para abrir o dossiê — os mesmos @ nas tabelas acima também levam até aqui.</p>'
                   f'<div class=aval-grid>{cards}</div></section>')
        dossies_html="".join(dossie_section(h,perfis[h],meta.get(h,{})) for h in ordem if h in perfis)

    render(saida,d,s,cambio,ktiles,viral_html,rows,comoviral,vrows,prows,recs,aval_html,dossies_html)

def render(saida,d,s,cambio,ktiles,viral_html,rows,comoviral,vrows,prows,recs,aval_html,dossies_html):
    CSS=r"""
:root{--paper:#FBFAF7;--surface:#FFF;--ink:#1B1E23;--ink-soft:#4A5057;--muted:#8A9099;--line:#E7E3DB;--teal:#0F766E;--teal-soft:#E7F0EE;--ochre:#B4712A;--ochre-soft:#F6ECDC;--shadow:0 1px 2px rgba(20,22,27,.04),0 8px 20px rgba(20,22,27,.06);
--serif:ui-serif,"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;--sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;--mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;}
@media (prefers-color-scheme:dark){:root{--paper:#121417;--surface:#191C21;--ink:#ECEEF0;--ink-soft:#B3B8BF;--muted:#7C838C;--line:#2A2E35;--teal:#3FB8A6;--teal-soft:#12312D;--ochre:#D69A54;--ochre-soft:#2A2114;--shadow:0 1px 2px rgba(0,0,0,.3),0 10px 26px rgba(0,0,0,.35);}}
:root[data-theme=dark]{--paper:#121417;--surface:#191C21;--ink:#ECEEF0;--ink-soft:#B3B8BF;--muted:#7C838C;--line:#2A2E35;--teal:#3FB8A6;--teal-soft:#12312D;--ochre:#D69A54;--ochre-soft:#2A2114;}
:root[data-theme=light]{--paper:#FBFAF7;--surface:#FFF;--ink:#1B1E23;--ink-soft:#4A5057;--muted:#8A9099;--line:#E7E3DB;--teal:#0F766E;--teal-soft:#E7F0EE;--ochre:#B4712A;--ochre-soft:#F6ECDC;}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55}
.wrap{max-width:1000px;margin:0 auto;padding:0 22px 48px}
h1,h2,h3{font-family:var(--serif);font-weight:600;letter-spacing:-.01em;margin:0}
.top{border-bottom:1px solid var(--line);background:var(--surface)}.top-in{max-width:1000px;margin:0 auto;padding:26px 22px}
.brand{font-family:var(--mono);font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-soft);display:flex;align-items:center;gap:9px}
.brand .dot{width:9px;height:9px;border-radius:50%;background:var(--teal)}
h1{font-size:1.9rem;margin:8px 0 2px}.sub{color:var(--ink-soft)}
.sec{padding:34px 0;border-bottom:1px solid var(--line)}.sec:last-child{border-bottom:0}
.eyebrow{font-family:var(--mono);font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--teal)}
h2{font-size:1.5rem;margin:.3em 0 .1em}.lead{font-family:var(--serif);font-size:1.2rem;line-height:1.5;max-width:66ch;margin-top:14px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:18px 0}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px;box-shadow:var(--shadow)}
.k-v{font-family:var(--mono);font-size:1.5rem;font-weight:600;font-variant-numeric:tabular-nums}.k-k{font-size:.78rem;color:var(--ink-soft);margin-top:2px}.k-n{font-family:var(--mono);font-size:.68rem;color:var(--muted);margin-top:3px}
.callout{background:var(--teal-soft);border:1px solid var(--teal);border-radius:12px;padding:14px 18px;margin-top:6px}
.callout .tag{display:inline-block;font-family:var(--mono);font-size:.64rem;letter-spacing:.08em;text-transform:uppercase;background:var(--teal);color:#fff;border-radius:6px;padding:2px 8px;margin-right:8px}
.tbl-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin-top:16px}
table{width:100%;border-collapse:collapse;font-size:.9rem}th,td{padding:10px 13px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-family:var(--mono);font-size:.64rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
tr:last-child td{border-bottom:0}.who b{display:block}.nome{color:var(--muted);font-size:.78rem}
tr.alvo{background:var(--ochre-soft)}tr.alvo .nome{color:var(--ochre)}
a{color:var(--teal);text-decoration:none}a:hover{text-decoration:underline}
.prod{max-width:360px}.prod a{font-weight:500}
.orig{display:block;font-family:var(--mono);font-size:.72rem;color:var(--muted);margin-top:2px}
.star{font-size:.74rem;color:var(--ochre);margin-top:3px}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px;box-shadow:var(--shadow)}
.card h3{font-size:1rem;margin-bottom:.5em}.card p{color:var(--ink-soft);font-size:.9rem;margin:.4em 0 0}
.note{color:var(--muted);font-size:.82rem;margin-top:10px}
.recs{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px}
.rec{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px 20px;box-shadow:var(--shadow)}
.rec .r-n{font-family:var(--mono);font-size:.8rem;color:var(--ochre)}.rec h3{color:var(--ink);margin:.3em 0 .4em;font-size:1.05rem}.rec p{color:var(--ink-soft);font-size:.92rem}
/* avaliações (índice) */
.aval-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:16px}
.aval-card{display:flex;flex-direction:column;gap:3px;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px;box-shadow:var(--shadow);color:var(--ink)}
.aval-card:hover{border-color:var(--teal);text-decoration:none}
.aval-card b{font-family:var(--mono);font-size:.9rem}
.aval-tag{font-family:var(--mono);font-size:.58rem;letter-spacing:.06em;background:var(--ochre);color:#fff;border-radius:5px;padding:1px 6px;margin-left:4px}
.aval-nome{color:var(--muted);font-size:.78rem}.go{color:var(--teal);font-size:.8rem;font-family:var(--mono);margin-top:4px}
/* dossiê */
.dossie{scroll-margin-top:16px}.dossie .dsub{color:var(--muted);font-size:1rem;font-weight:400}
.dossie .bio{color:var(--ink-soft);font-size:.9rem;margin-top:6px;white-space:pre-line;max-width:70ch}
.dossie .lead{font-size:1.05rem}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px}
.tops{list-style:none;margin:0;padding:0}
.tops li{padding:9px 0;border-top:1px solid var(--line)}.tops li:first-child{border-top:0}
.tv-t{font-size:.86rem;line-height:1.35}.tv-s{font-family:var(--mono);font-size:.72rem;color:var(--muted);margin-top:3px;font-variant-numeric:tabular-nums}
.chips{display:flex;flex-wrap:wrap;gap:7px}
.chip{display:inline-flex;align-items:center;gap:5px;background:var(--teal-soft);color:var(--teal);border-radius:999px;padding:4px 10px;font-family:var(--mono);font-size:.76rem}.chip-n{opacity:.6;font-size:.68rem}
.back{margin-top:14px;font-family:var(--mono);font-size:.8rem}
.foot{max-width:1000px;margin:0 auto;padding:22px;color:var(--muted);font-size:.78rem}
.toggle{position:fixed;top:14px;right:14px;background:var(--surface);border:1px solid var(--line);color:var(--ink-soft);border-radius:999px;padding:6px 11px;font-family:var(--mono);font-size:.72rem;cursor:pointer}
@media (max-width:720px){.cards,.recs,.two{grid-template-columns:1fr}}
@media print{.toggle{display:none}}
"""
    JS=("(function(){var b=document.getElementById('tg');if(!b)return;b.onclick=function(){var r=document.documentElement,"
        "d=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');"
        "r.setAttribute('data-theme',d==='dark'?'light':'dark');};})();")
    pnota=d.get("produtos_nota","")
    cambio_nota=(f'<p class=note>Preços convertidos de US$ para R$ ao câmbio de referência '
                 f'<b>US$ 1 = {brl(cambio)}</b> — os produtos são do mercado global (TikTok Shop US); '
                 f'trate como <b>sinal de categoria</b> e valide preço/fornecedor no Brasil.</p>')
    doc=f"""<!doctype html><html lang=pt-BR><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1"><title>Divisão Shop — {esc(s.get("nome") or s.get("handle"))}</title>
<style>{CSS}</style></head><body>
<button class=toggle id=tg>◑ Tema</button>
<header class=top><div class=top-in>
<div class=brand><span class=dot></span> FullBPO · Divisão Shop</div>
<h1>Estudo estratégico — {esc(s.get("nome") or "")} <span style="color:var(--muted);font-size:1rem">@{esc(s.get("handle"))}</span></h1>
<div class=sub>{esc(d.get("cliente",""))} · {esc(d.get("data",""))}</div>
</div></header>
<main class=wrap>
<section class=sec><span class=eyebrow>Onde ela está</span>
<div class=lead>{paras(d.get("resumo"))}</div>
<div class=kpis>{ktiles}</div>{viral_html}</section>

<section class=sec id=mapa><span class=eyebrow>01 · Como a concorrência viraliza</span>
<h2>Priscila vs. o nicho</h2>
<p class=note>Clique num <b>@perfil</b> para abrir o dossiê completo dele.</p>
<div class=tbl-wrap><table><thead><tr><th>Creator</th><th class=num>Seguidores</th><th class=num>Views (med)</th><th class=num>Engaj</th><th class=num>Melhor vídeo</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class=cards>{comoviral}</div></section>

<section class=sec><span class=eyebrow>02 · Vídeos virais do nicho</span>
<h2>O que estourou (e por quê)</h2>
<div class=tbl-wrap><table><thead><tr><th class=num>Múlt.</th><th class=num>Views</th><th>Creator</th><th>Vídeo</th></tr></thead><tbody>{vrows}</tbody></table></div>
<p class=note>{rich(d.get("padrao_virais",""))}</p></section>

<section class=sec><span class=eyebrow>03 · Produtos que vendem no nicho</span>
<h2>O que ela pode adotar</h2>
<div class=tbl-wrap><table><thead><tr><th>Produto</th><th class=num>Vendas</th><th class=num>Preço</th><th>Loja</th></tr></thead><tbody>{prows}</tbody></table></div>
{cambio_nota}
<p class=note>{rich(pnota)}</p></section>

<section class=sec><span class=eyebrow>Plano</span>
<h2>Recomendações pra Priscila</h2>
<div class=recs>{recs}</div></section>
{aval_html}
{dossies_html}
</main>
<footer class=foot>FullBPO — Backoffice Inteligente · Divisão Shop · dados públicos via Apify (estimativas) · uso interno/cliente.</footer>
<script>{JS}</script></body></html>"""
    open(saida,"w",encoding="utf-8").write(doc)
    print(f"dash Shop gerado: {saida} ({os.path.getsize(saida)//1024} KB)")

if __name__=="__main__":
    main()
