#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# montar_shop.py — Frente 1 (Shop): dash estratégico CENTRADO EM 1 CREATOR.
# Responde, para o creator-alvo (ex.: a cliente Priscila): onde ela está,
# COMO A CONCORRÊNCIA VIRALIZA, QUAIS VÍDEOS VIRALIZAM no nicho e QUAIS
# PRODUTOS vendem bem e ela pode adotar — com recomendações.
#
# Uso: montar_shop.py <shop.json> [saida.html]
# Esquema do shop.json: ver SKILL.md (mapa-nicho).
# ---------------------------------------------------------------------------
import sys, os, json, html

def esc(s): return html.escape(str(s if s is not None else ""), quote=True)
def bi(n):
    try: return f"{int(n):,}".replace(",", ".")
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

def main():
    if len(sys.argv)<2:
        print("uso: montar_shop.py <shop.json> [saida.html]",file=sys.stderr); sys.exit(2)
    d=json.load(open(sys.argv[1],encoding="utf-8"))
    saida=sys.argv[2] if len(sys.argv)>2 else "shop.html"
    s=d.get("subject",{})

    # bloco 0 — KPIs do alvo
    kpis=[("Seguidores",bi(s.get("seguidores")),""),
          ("Views (mediana)",bi(s.get("mediana")),"alcance típico"),
          ("Melhor vídeo",bi(s.get("melhor")),"o teto dela"),
          ("Engajamento",f'{str(s.get("engajamento","")).replace(".",",")}%',""),
          ("Cadência",f'{str(s.get("cadencia","")).replace(".",",")}/sem',""),
          ("Duração méd",f'{s.get("duracao")}s',"")]
    ktiles="".join(f'<div class=kpi><div class=k-v>{v}</div><div class=k-k>{esc(l)}</div>'
                   f'{f"<div class=k-n>{esc(n)}</div>" if n else ""}</div>' for l,v,n in kpis)
    viral=s.get("viral") or {}
    viral_html=(f'<div class="callout"><span class=tag>Prova de que dá</span>'
                f'<b>Ela já viralizou:</b> <a href="{esc(viral.get("url"))}">{esc(viral.get("titulo"))}</a> — '
                f'<b>{bi(viral.get("views"))} views</b> ({esc(viral.get("multiplo"))}× a mediana).</div>') if viral else ""

    # bloco 1 — concorrência lado a lado (alvo + concorrentes)
    def linha(p,alvo=False):
        cls=' class="alvo"' if alvo else ''
        return (f'<tr{cls}><td class=who><b>@{esc(p.get("handle"))}</b>'
                f'<span class=nome>{esc(p.get("nome") or "")}{" · ALVO" if alvo else ""}</span></td>'
                f'<td class=num>{bi(p.get("seguidores"))}</td><td class=num>{bi(p.get("mediana"))}</td>'
                f'<td class=num>{str(p.get("engajamento","")).replace(".",",")}%</td>'
                f'<td class=num>{bi(p.get("melhor"))}</td></tr>')
    rows=linha(s,alvo=True)+"".join(linha(c) for c in d.get("concorrentes",[]))
    comoviral="".join(
        f'<div class=card><b>@{esc(c.get("handle"))}</b><p>{rich(c.get("como_viraliza"))}</p></div>'
        for c in d.get("concorrentes",[]) if c.get("como_viraliza"))

    # bloco 2 — vídeos virais do nicho
    vrows="".join(
        f'<tr><td class=num><b>{esc(v.get("multiplo"))}×</b></td><td class=num>{bi(v.get("views"))}</td>'
        f'<td>@{esc(v.get("handle"))}</td><td><a href="{esc(v.get("url"))}">{esc(v.get("titulo"))}</a></td></tr>'
        for v in d.get("virais_nicho",[]))

    # bloco 3 — produtos do nicho
    prows=""
    for p in d.get("produtos_nicho",[]):
        prows+=(f'<tr><td>{esc(p.get("produto"))}</td><td class=num><b>{bi(p.get("vendas"))}</b></td>'
                f'<td class=num>{esc(p.get("preco"))} {esc(p.get("moeda"))}</td><td>{esc(p.get("loja"))}</td></tr>')

    # bloco 4 — recomendações
    recs=""
    for i,r in enumerate(d.get("recomendacoes",[]),1):
        recs+=f'<div class=rec><span class=r-n>{i:02d}</span><h3>{rich(r.get("titulo"))}</h3>{paras(r.get("texto"))}</div>'

    render(saida,d,s,ktiles,viral_html,rows,comoviral,vrows,prows,recs)

def render(saida,d,s,ktiles,viral_html,rows,comoviral,vrows,prows,recs):
    CSS=r"""
:root{--paper:#FBFAF7;--surface:#FFF;--ink:#1B1E23;--ink-soft:#4A5057;--muted:#8A9099;--line:#E7E3DB;--teal:#0F766E;--teal-soft:#E7F0EE;--ochre:#B4712A;--ochre-soft:#F6ECDC;--shadow:0 1px 2px rgba(20,22,27,.04),0 8px 20px rgba(20,22,27,.06);
--serif:ui-serif,"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;--sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;--mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;}
@media (prefers-color-scheme:dark){:root{--paper:#121417;--surface:#191C21;--ink:#ECEEF0;--ink-soft:#B3B8BF;--muted:#7C838C;--line:#2A2E35;--teal:#3FB8A6;--teal-soft:#12312D;--ochre:#D69A54;--ochre-soft:#2A2114;--shadow:0 1px 2px rgba(0,0,0,.3),0 10px 26px rgba(0,0,0,.35);}}
:root[data-theme=dark]{--paper:#121417;--surface:#191C21;--ink:#ECEEF0;--ink-soft:#B3B8BF;--muted:#7C838C;--line:#2A2E35;--teal:#3FB8A6;--teal-soft:#12312D;--ochre:#D69A54;--ochre-soft:#2A2114;}
:root[data-theme=light]{--paper:#FBFAF7;--surface:#FFF;--ink:#1B1E23;--ink-soft:#4A5057;--muted:#8A9099;--line:#E7E3DB;--teal:#0F766E;--teal-soft:#E7F0EE;--ochre:#B4712A;--ochre-soft:#F6ECDC;}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55}
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
table{width:100%;border-collapse:collapse;font-size:.9rem}th,td{padding:10px 13px;border-bottom:1px solid var(--line);text-align:left}
th{font-family:var(--mono);font-size:.64rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
tr:last-child td{border-bottom:0}.who b{display:block}.nome{color:var(--muted);font-size:.78rem}
tr.alvo{background:var(--ochre-soft)}tr.alvo .nome{color:var(--ochre)}
a{color:var(--teal);text-decoration:none}a:hover{text-decoration:underline}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px;box-shadow:var(--shadow)}
.card p{color:var(--ink-soft);font-size:.9rem;margin:.4em 0 0}
.note{color:var(--muted);font-size:.82rem;margin-top:10px}
.recs{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px}
.rec{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px 20px;box-shadow:var(--shadow)}
.rec .r-n{font-family:var(--mono);font-size:.8rem;color:var(--ochre)}.rec h3{color:var(--ink);margin:.3em 0 .4em;font-size:1.05rem}.rec p{color:var(--ink-soft);font-size:.92rem}
.foot{max-width:1000px;margin:0 auto;padding:22px;color:var(--muted);font-size:.78rem}
.toggle{position:fixed;top:14px;right:14px;background:var(--surface);border:1px solid var(--line);color:var(--ink-soft);border-radius:999px;padding:6px 11px;font-family:var(--mono);font-size:.72rem;cursor:pointer}
@media (max-width:720px){.cards,.recs{grid-template-columns:1fr}}
@media print{.toggle{display:none}}
"""
    JS=("(function(){var b=document.getElementById('tg');if(!b)return;b.onclick=function(){var r=document.documentElement,"
        "d=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');"
        "r.setAttribute('data-theme',d==='dark'?'light':'dark');};})();")
    pnota=d.get("produtos_nota","")
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

<section class=sec><span class=eyebrow>01 · Como a concorrência viraliza</span>
<h2>Priscila vs. o nicho</h2>
<div class=tbl-wrap><table><thead><tr><th>Creator</th><th class=num>Seguidores</th><th class=num>Views (med)</th><th class=num>Engaj</th><th class=num>Melhor vídeo</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class=cards>{comoviral}</div></section>

<section class=sec><span class=eyebrow>02 · Vídeos virais do nicho</span>
<h2>O que estourou (e por quê)</h2>
<div class=tbl-wrap><table><thead><tr><th class=num>Múlt.</th><th class=num>Views</th><th>Creator</th><th>Vídeo</th></tr></thead><tbody>{vrows}</tbody></table></div>
<p class=note>{rich(d.get("padrao_virais",""))}</p></section>

<section class=sec><span class=eyebrow>03 · Produtos que vendem no nicho</span>
<h2>O que ela pode adotar</h2>
<div class=tbl-wrap><table><thead><tr><th>Produto</th><th class=num>Vendas</th><th class=num>Preço</th><th>Loja</th></tr></thead><tbody>{prows}</tbody></table></div>
<p class=note>{rich(pnota)}</p></section>

<section class=sec><span class=eyebrow>Plano</span>
<h2>Recomendações pra Priscila</h2>
<div class=recs>{recs}</div></section>
</main>
<footer class=foot>FullBPO — Backoffice Inteligente · Divisão Shop · dados públicos via Apify (estimativas) · uso interno/cliente.</footer>
<script>{JS}</script></body></html>"""
    open(saida,"w",encoding="utf-8").write(doc)
    print(f"dash Shop gerado: {saida} ({os.path.getsize(saida)//1024} KB)")

if __name__=="__main__":
    main()
