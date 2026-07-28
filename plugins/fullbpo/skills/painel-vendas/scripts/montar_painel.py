#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# montar_painel.py — monta o "Painel de Vendas" da FullBPO (TikTok Shop) como
# HTML AUTOCONTIDO, com gráficos em SVG inline (sem libs/CDN). Consome um
# vendas.json NORMALIZADO — de onde vier o dado (CSV do Affiliate Center ou
# API de terceiros como EchoTik/FastMoss) é problema do adaptador, não daqui.
#
# Uso:  python3 montar_painel.py <vendas.json> [saida.html]
# Esquema do vendas.json: ver SKILL.md (painel-vendas).
# ---------------------------------------------------------------------------
import sys, os, json, html

def esc(s): return html.escape(str(s if s is not None else ""), quote=True)

def brl(v, cents=False):
    try: v = float(v)
    except (TypeError, ValueError): return esc(v)
    s = f"{v:,.2f}" if cents else f"{v:,.0f}"
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"R$ {s}"

def pct(v):
    s = f"{float(v):.1f}".replace(".", ",")
    return f"{s}%"

# ---------- helpers de SVG (usam as CSS vars do tema) ----------------------
def svg_bars(vals, w=680, h=150, pad=6):
    if not vals: return ""
    mx = max(vals) or 1
    n = len(vals); bw = (w - pad*(n+1)) / n
    bars = []
    for i, v in enumerate(vals):
        bh = (v / mx) * (h - 14)
        x = pad + i*(bw+pad); y = h - bh
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="2" fill="var(--teal)" opacity="0.85"/>')
    return f'<svg viewBox="0 0 {w} {h}" class="chart" preserveAspectRatio="none" role="img">{"".join(bars)}</svg>'

def svg_area(cum, meta=None, w=680, h=170):
    if not cum: return ""
    mx = max(max(cum), meta or 0) or 1
    n = len(cum); step = w/(n-1) if n > 1 else w
    pts = [(i*step, h - (v/mx)*(h-16)) for i, v in enumerate(cum)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"0,{h} " + line + f" {w},{h}"
    out = [f'<polygon points="{area}" fill="var(--teal)" opacity="0.10"/>',
           f'<polyline points="{line}" fill="none" stroke="var(--teal)" stroke-width="2.5"/>']
    if meta:
        my = h - (meta/mx)*(h-16)
        out.append(f'<line x1="0" y1="{my:.1f}" x2="{w}" y2="{my:.1f}" stroke="var(--ochre)" stroke-width="1.5" stroke-dasharray="5 4"/>')
    ex, ey = pts[-1]
    out.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="4" fill="var(--teal)"/>')
    return f'<svg viewBox="0 0 {w} {h}" class="chart" preserveAspectRatio="none" role="img">{"".join(out)}</svg>'

def svg_pareto(vals, w=680, h=170):
    if not vals: return ""
    tot = sum(vals) or 1; mx = max(vals) or 1
    n = len(vals); pad = 3; bw = (w - pad*(n+1)) / n
    bars, cum, run = [], [], 0
    for i, v in enumerate(vals):
        bh = (v/mx)*(h-16); x = pad + i*(bw+pad)
        bars.append(f'<rect x="{x:.1f}" y="{h-bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="1.5" fill="var(--teal)" opacity="0.8"/>')
        run += v; cum.append((x+bw/2, h - (run/tot)*(h-16)))
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in cum)
    y80 = h - 0.8*(h-16)
    return (f'<svg viewBox="0 0 {w} {h}" class="chart" preserveAspectRatio="none" role="img">{"".join(bars)}'
            f'<line x1="0" y1="{y80:.1f}" x2="{w}" y2="{y80:.1f}" stroke="var(--muted)" stroke-width="1" stroke-dasharray="4 4"/>'
            f'<polyline points="{line}" fill="none" stroke="var(--ochre)" stroke-width="2"/></svg>')

def svg_donut(segs, size=150):
    tot = sum(v for _, v, _ in segs) or 1
    r = size/2 - 14; c = 2*3.14159*r; cx = cy = size/2
    circles, off = [], 0.0
    for _, v, col in segs:
        frac = v/tot; dash = frac*c
        circles.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="{col}" stroke-width="16" '
            f'stroke-dasharray="{dash:.2f} {c-dash:.2f}" stroke-dashoffset="{-off:.2f}" '
            f'transform="rotate(-90 {cx} {cy})"/>')
        off += dash
    return f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" role="img">{"".join(circles)}</svg>'

def panel(titulo, sub, inner, extra=""):
    return (f'<div class="panel{extra}"><div class="p-head"><h3>{esc(titulo)}</h3>'
            f'{f"<span class=p-sub>{esc(sub)}</span>" if sub else ""}</div>{inner}</div>')

def main():
    if len(sys.argv) < 2:
        print("uso: montar_painel.py <vendas.json> [saida.html]", file=sys.stderr); sys.exit(2)
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    out_path = sys.argv[2] if len(sys.argv) > 2 else "painel.html"
    if d.get("aguardando"):                 # creator sem vendas ainda -> painel honesto (sem número inventado)
        _render_aguardando(d, out_path); return
    k = d.get("kpis", {})
    meta = d.get("meta_gmv")

    # KPIs
    kdefs = [("gmv","GMV no mês",brl(k.get("gmv"))),
             ("comissao","Comissão",brl(k.get("comissao"))),
             ("itens","Itens vendidos", f'{int(k.get("itens",0)):,}'.replace(",",".")),
             ("ticket","Ticket médio", brl(k.get("ticket"), cents=True)),
             ("gmv_dia","GMV por dia", brl(k.get("gmv_dia"))),
             ("inelegivel_pct","% Inelegível", pct(k.get("inelegivel_pct",0)))]
    kpis = "".join(
        f'<div class="kpi{ " warn" if key=="inelegivel_pct" else "" }"><div class="k-v">{val}</div>'
        f'<div class="k-k">{esc(lbl)}</div></div>' for key, lbl, val in kdefs)

    # GMV acumulado
    diario = [x.get("gmv",0) for x in d.get("gmv_diario", [])]
    cum, run = [], 0
    for v in diario: run += v; cum.append(run)
    falta = (meta - (k.get("gmv") or (cum[-1] if cum else 0))) if meta else None
    gmv_sub = f'meta {brl(meta)} · faltam {brl(falta)}' if meta and falta and falta>0 else (f'meta {brl(meta)} · batida' if meta else '')
    acum = panel("GMV acumulado — ritmo do mês", gmv_sub, svg_area(cum, meta), " wide")

    ritmo = panel("Ritmo diário", f'{len(diario)} dias', svg_bars(diario), " wide")

    # Pareto
    par = sorted(d.get("pareto", []), key=lambda x: -x.get("comissao",0))
    par_vals = [p.get("comissao",0) for p in par]
    tot = sum(par_vals) or 1; run=0; n80=0
    for v in par_vals:
        run += v; n80 += 1
        if run/tot >= 0.8: break
    pareto = panel("Pareto de produtos — comissão", f'{n80} produtos = 80%', svg_pareto(par_vals))

    # Status donut
    st = d.get("status", {})
    segs = [("Liquidado", st.get("liquidado",0), "var(--teal)"),
            ("Pendente", st.get("pendente",0), "var(--muted)"),
            ("Inelegível", st.get("inelegivel",0), "var(--ochre)")]
    tot_st = sum(v for _,v,_ in segs) or 1
    leg = "".join(
        f'<li><span class="dot" style="background:{c}"></span>{esc(l)}'
        f'<span class="leg-v">{brl(v)} · {pct(v/tot_st*100)}</span></li>' for l,v,c in segs)
    donut = panel("Composição por status", "",
                  f'<div class="donut-wrap">{svg_donut(segs)}<ul class="legend">{leg}</ul></div>')

    # Fornecedores
    forn = sorted(d.get("fornecedores", []), key=lambda x: -x.get("gmv",0))
    fmax = max((f.get("gmv",0) for f in forn), default=1) or 1
    frows = ""
    for f in forn[:12]:
        neg = f.get("negociavel")
        bar = (f.get("gmv",0)/fmax)*100
        frows += (f'<tr class="{ "neg" if neg else "" }"><td>{esc(f.get("nome"))}</td>'
                  f'<td class="num"><span class="minibar" style="width:{bar:.0f}%"></span>{brl(f.get("gmv"))}</td>'
                  f'<td class="num">{pct(f.get("com_padrao",0))}</td>'
                  f'<td class="num">{pct(f.get("com_ads",0))}</td>'
                  f'<td class="num">{"🟡 negociar" if neg else "—"}</td></tr>')
    forn_tbl = panel("Fornecedores", "80% do GMV · comissão padrão vs. ads (amarelo = negociar)",
        f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Fornecedor</th><th class="num">GMV</th>'
        f'<th class="num">Padrão</th><th class="num">Ads</th><th class="num">Ação</th></tr></thead>'
        f'<tbody>{frows}</tbody></table></div>', " wide")

    # Apostas
    ap = d.get("apostas", [])
    arows = ""
    for a in ap:
        tag = a.get("tag","")
        cls = "novo" if tag.lower()=="novo" else "acel"
        arows += (f'<li><span class="ap-tag {cls}">{esc(tag)}</span>'
                  f'<span class="ap-nome">{esc(a.get("produto"))}</span>'
                  f'<span class="ap-v">{brl(a.get("gmv_esperado"))} <small>esperado</small></span></li>')
    apostas = panel("Apostas — fora do topo, mas acelerando", "produtos que venderam rápido sem ser campeões",
                    f'<ul class="apostas">{arows}</ul>', " wide")

    render(out_path, d, kpis, acum, ritmo, pareto, donut, forn_tbl, apostas)

def _render_aguardando(d, out_path):
    # Painel HONESTO p/ creator que ainda não vende pelo Shop: identidade + estrutura
    # + POTENCIAL com dado REAL do nicho. Nada de GMV/venda inventado (o oposto do demo).
    lbls = ["GMV no mês", "Comissão", "Itens vendidos", "Ticket médio", "GMV por dia", "% Inelegível"]
    kpis = "".join(f'<div class="kpi"><div class="k-v" style="color:var(--muted)">—</div>'
                   f'<div class="k-k">{esc(l)}</div></div>' for l in lbls)

    passos = d.get("passos") or [
        "TikTok Affiliate Center → Dados/Analytics → exportar o CSV do mês",
        "Enviar o CSV pra FullBPO (ou salvar na pasta combinada)",
        "O painel popula sozinho: GMV, comissão, Pareto de produtos e fornecedores a negociar",
    ]
    p1 = panel("Este painel já está pronto — falta só o seu 1º dado de vendas",
               "popula com o CSV do Affiliate Center",
               '<p style="margin:.1em 0 1em;color:var(--ink-soft)">Enquanto você não vende pelo Shop, a gente '
               '<b>não inventa número</b>. Assim que chegar o 1º relatório do Affiliate Center, tudo aqui vira o seu real:</p>'
               f'<ol style="margin:0;padding-left:1.2em;color:var(--ink-soft);line-height:1.9">'
               f'{"".join(f"<li>{esc(p)}</li>" for p in passos)}</ol>', " wide")

    pot = d.get("potencial") or {}
    linhas = ""
    if pot.get("minha_mediana") and pot.get("mediana_nicho"):
        mine, nicho = pot["minha_mediana"], pot["mediana_nicho"]
        mult = round(nicho / mine, 1) if mine else 0
        bar = max(2, mine / nicho * 100)
        linhas = (
            f'<p style="margin:.1em 0 1em;color:var(--ink-soft)">O que separa você de vender no Shop hoje '
            f'<b>não é preço nem produto — é alcance</b>. Comparando com dado real do seu nicho:</p>'
            f'<div style="display:flex;flex-direction:column;gap:12px">'
            f'<div><div class="k-k">Sua mediana de views/vídeo</div>'
            f'<div style="height:14px;background:var(--teal);border-radius:3px;width:{bar:.1f}%;min-width:26px"></div>'
            f'<div class="p-sub" style="text-align:left">{int(mine):,} views</div></div>'
            f'<div><div class="k-k">Mediana do nicho (creators do mesmo tema)</div>'
            f'<div style="height:14px;background:var(--ochre);border-radius:3px;width:100%"></div>'
            f'<div class="p-sub" style="text-align:left">{int(nicho):,} views · você está <b>{mult}× atrás</b></div></div>'
            f'</div>'.replace(",", "."))
    if pot.get("obs"):
        linhas += f'<p style="margin:1em 0 0;color:var(--ink-soft)">{esc(pot["obs"])}</p>'
    p2 = panel("Seu potencial — com dado real do nicho", "não é promessa; é a distância a fechar",
               linhas or '<p style="color:var(--muted)">Sem benchmark de nicho ainda.</p>', " wide")

    glos = [("GMV", "o quanto você vendeu no mês (soma dos pedidos)"),
            ("Comissão", "o que de fato entra pra você, por faixa de produto"),
            ("Pareto", "os poucos produtos que fazem 80% da comissão — onde focar"),
            ("Fornecedores", "quais dá pra negociar comissão maior (padrão vs. ads)"),
            ("% Inelegível", "vendas que não contam comissão — pra você cortar")]
    p3 = panel("O que cada número vai te mostrar", "",
               '<ul class="legend">' + "".join(
                   f'<li><span class="dot" style="background:var(--teal)"></span>{esc(t)}'
                   f'<span class="leg-v" style="color:var(--ink-soft)">{esc(v)}</span></li>' for t, v in glos)
               + '</ul>', " wide")

    render(out_path, d, kpis, p1, p2, p3, "", "", "")


def render(out_path, d, kpis, acum, ritmo, pareto, donut, forn_tbl, apostas):
    titulo = f'Painel de Vendas — {d.get("handle") or d.get("cliente","")}'.strip(" —")
    CSS = r"""
:root{--paper:#FBFAF7;--surface:#FFFFFF;--ink:#1B1E23;--ink-soft:#4A5057;--muted:#8A9099;
--line:#E7E3DB;--teal:#0F766E;--teal-soft:#E7F0EE;--ochre:#B4712A;--ochre-soft:#F6ECDC;
--shadow:0 1px 2px rgba(20,22,27,.04),0 8px 20px rgba(20,22,27,.06);
--serif:ui-serif,"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
--sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
--mono:ui-monospace,"SF Mono","Cascadia Code","Roboto Mono",Menlo,Consolas,monospace;}
@media (prefers-color-scheme:dark){:root{--paper:#121417;--surface:#191C21;--ink:#ECEEF0;--ink-soft:#B3B8BF;
--muted:#7C838C;--line:#2A2E35;--teal:#3FB8A6;--teal-soft:#12312D;--ochre:#D69A54;--ochre-soft:#2A2114;
--shadow:0 1px 2px rgba(0,0,0,.3),0 10px 26px rgba(0,0,0,.35);}}
:root[data-theme="light"]{--paper:#FBFAF7;--surface:#FFFFFF;--ink:#1B1E23;--ink-soft:#4A5057;--muted:#8A9099;--line:#E7E3DB;--teal:#0F766E;--teal-soft:#E7F0EE;--ochre:#B4712A;--ochre-soft:#F6ECDC;}
:root[data-theme="dark"]{--paper:#121417;--surface:#191C21;--ink:#ECEEF0;--ink-soft:#B3B8BF;--muted:#7C838C;--line:#2A2E35;--teal:#3FB8A6;--teal-soft:#12312D;--ochre:#D69A54;--ochre-soft:#2A2114;}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:0 22px 48px}
h1,h3{font-family:var(--serif);font-weight:600;letter-spacing:-.01em;margin:0}
/* header */
.top{border-bottom:1px solid var(--line);background:var(--surface)}
.top-in{max-width:1080px;margin:0 auto;padding:24px 22px;display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap}
.brand{font-family:var(--mono);font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-soft);display:flex;align-items:center;gap:9px}
.brand .dot{width:9px;height:9px;border-radius:50%;background:var(--teal)}
.top h1{font-size:1.7rem;margin-top:8px}
.top .who{color:var(--ink-soft);font-size:.95rem}
.mes{font-family:var(--mono);font-size:.82rem;color:var(--teal);background:var(--teal-soft);padding:7px 14px;border-radius:999px}
/* kpi */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:22px 0}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:15px 17px;box-shadow:var(--shadow)}
.kpi.warn{border-color:var(--ochre)}
.k-v{font-family:var(--mono);font-size:1.55rem;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.kpi.warn .k-v{color:var(--ochre)}
.k-k{font-size:.78rem;color:var(--ink-soft);margin-top:3px}
/* grid of panels */
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px 20px;box-shadow:var(--shadow)}
.panel.wide{grid-column:1/-1}
.p-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-bottom:14px}
.p-head h3{font-size:1.05rem;color:var(--ink)}
.p-sub{font-family:var(--mono);font-size:.72rem;color:var(--muted);text-align:right}
.chart{width:100%;height:auto;display:block}
/* donut */
.donut-wrap{display:flex;align-items:center;gap:22px;flex-wrap:wrap}
.legend{list-style:none;margin:0;padding:0;flex:1;min-width:180px}
.legend li{display:flex;align-items:center;gap:8px;padding:6px 0;font-size:.9rem;border-top:1px solid var(--line)}
.legend li:first-child{border-top:0}
.legend .dot{width:10px;height:10px;border-radius:2px;flex:none}
.legend .leg-v{margin-left:auto;font-family:var(--mono);font-size:.8rem;color:var(--ink-soft);font-variant-numeric:tabular-nums}
/* table */
.tbl-wrap{overflow-x:auto}
.tbl{width:100%;border-collapse:collapse;font-size:.88rem}
.tbl th{text-align:left;font-family:var(--mono);font-size:.66rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding:6px 10px;border-bottom:1px solid var(--line)}
.tbl td{padding:8px 10px;border-bottom:1px solid var(--line)}
.tbl .num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
.tbl tr.neg{background:var(--ochre-soft)}
.minibar{display:inline-block;height:7px;background:var(--teal);border-radius:2px;margin-right:8px;vertical-align:middle;opacity:.55}
/* apostas */
.apostas{list-style:none;margin:0;padding:0}
.apostas li{display:flex;align-items:center;gap:12px;padding:10px 0;border-top:1px solid var(--line)}
.apostas li:first-child{border-top:0}
.ap-tag{font-family:var(--mono);font-size:.66rem;letter-spacing:.05em;padding:3px 8px;border-radius:6px;flex:none;text-transform:uppercase}
.ap-tag.novo{background:var(--teal-soft);color:var(--teal)}
.ap-tag.acel{background:var(--ochre-soft);color:var(--ochre)}
.ap-nome{flex:1;font-size:.92rem}
.ap-v{font-family:var(--mono);font-size:.9rem;font-weight:600;font-variant-numeric:tabular-nums}
.ap-v small{font-weight:400;color:var(--muted)}
/* foot + toggle */
.foot{max-width:1080px;margin:0 auto;padding:8px 22px;color:var(--muted);font-size:.76rem}
.toggle{position:fixed;top:14px;right:14px;z-index:9;background:var(--surface);border:1px solid var(--line);color:var(--ink-soft);border-radius:999px;padding:6px 11px;font-family:var(--mono);font-size:.72rem;cursor:pointer;box-shadow:var(--shadow)}
.toggle:hover{color:var(--teal)}
:focus-visible{outline:2px solid var(--teal);outline-offset:2px}
@media (max-width:760px){.grid{grid-template-columns:1fr}.top h1{font-size:1.4rem}}
@media print{.toggle{display:none}body{background:#fff}.panel,.kpi{box-shadow:none;break-inside:avoid}}
"""
    JS = ("(function(){var b=document.getElementById('tg');if(!b)return;b.onclick=function(){"
          "var r=document.documentElement,d=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');"
          "var n=d==='dark'?'light':'dark';r.setAttribute('data-theme',n);b.textContent=n==='dark'?'\\u25D0 Tema':'\\u25D1 Tema';};})();")
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(titulo)}</title>
<style>{CSS}</style></head><body>
<button class="toggle" id="tg" aria-label="Alternar tema">◑ Tema</button>
<header class="top"><div class="top-in"><div>
<div class="brand"><span class="dot"></span> FullBPO · Painel de Vendas</div>
<h1>{esc(d.get("cliente") or d.get("handle","Painel de Vendas"))}</h1>
<div class="who">Afiliação TikTok Shop{f' · {esc(d.get("handle"))}' if d.get("handle") else ''}</div>
</div><div class="mes">{esc(d.get("mes",""))}</div></div></header>
<main class="wrap">
<div class="kpis">{kpis}</div>
<div class="grid">
{acum}
{ritmo}
{pareto}
{donut}
{forn_tbl}
{apostas}
</div>
</main>
<footer class="foot">Gerado pela FullBPO — Backoffice Inteligente · dados: {esc(d.get("fonte","—"))} · valores em BRL. Uso interno/cliente.</footer>
<script>{JS}</script></body></html>"""
    open(out_path, "w", encoding="utf-8").write(doc)
    print(f"painel gerado: {out_path} ({os.path.getsize(out_path)//1024} KB)")

if __name__ == "__main__":
    main()
