#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# montar_mapa.py — Frente 1 (TikTok Shop): monta o "mapa competitivo do nicho"
# comparando N perfis lado a lado (posicionamento · tração · [produtos]).
# HTML autocontido, mesma identidade dos outros renderizadores.
#
# Uso: montar_mapa.py <pasta_nicho> [saida.html] [--titulo "Nicho X"]
#   <pasta_nicho> = pasta com vários perfil_analise.json (1 por creator),
#   ex.: a saída do coleta-apify/scripts/coletar_nicho.sh.
# ---------------------------------------------------------------------------
import sys, os, glob, json, html

def esc(s): return html.escape(str(s if s is not None else ""), quote=True)
def bi(n):
    try: return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError): return "—"

def carregar(pasta):
    perfis = []
    for f in sorted(glob.glob(os.path.join(pasta, "*.json"))):
        if os.path.basename(f) in ("produtos.json", "nicho.json"): continue
        try: d = json.load(open(f, encoding="utf-8"))
        except Exception: continue
        if d.get("handle"): perfis.append(d)
    return perfis

COLS = [
    ("seguidores", "Seguidores", lambda p: p.get("seguidores")),
    ("mediana",    "Views (mediana)", lambda p: (p.get("views") or {}).get("mediana")),
    ("engaj",      "Engajamento", lambda p: p.get("engajamento_proxy")),
    ("cadencia",   "Cadência/sem", lambda p: p.get("cadencia_semana")),
    ("melhor",     "Melhor vídeo", lambda p: (p.get("views") or {}).get("max")),
    ("duracao",    "Duração méd", lambda p: p.get("duracao_media")),
]

def fmt(col, v):
    if v is None: return "—"
    if col == "engaj": return f'{str(v).replace(".", ",")}%'
    if col == "cadencia": return f'{str(v).replace(".", ",")}/sem'
    if col == "duracao": return f'{v}s'
    return bi(v)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta = args[0] if args else "."
    saida = args[1] if len(args) > 1 else "mapa.html"
    titulo = "Nicho"
    if "--titulo" in sys.argv: titulo = sys.argv[sys.argv.index("--titulo")+1]
    perfis = carregar(pasta)
    if not perfis:
        print(f"ERRO: nenhum perfil_analise.json em {pasta}", file=sys.stderr); sys.exit(3)
    perfis.sort(key=lambda p: -(p.get("seguidores") or 0))

    # líder por coluna (maior valor)
    lead = {}
    for key, _, get in COLS:
        vals = [(get(p) or 0, i) for i, p in enumerate(perfis)]
        lead[key] = max(vals)[1] if vals else -1

    # cabeçalho da tabela
    ths = "".join(f"<th class=num>{esc(lbl)}</th>" for _, lbl, _ in COLS)
    rows = ""
    for i, p in enumerate(perfis):
        tds = ""
        for key, _, get in COLS:
            cls = "num lead" if lead.get(key) == i else "num"
            tds += f'<td class="{cls}">{fmt(key, get(p))}</td>'
        rows += (f'<tr><td class="who"><b>@{esc(p.get("handle"))}</b>'
                 f'<span class="nome">{esc(p.get("nome") or "")}</span></td>{tds}</tr>')

    # cards de posicionamento
    cards = ""
    for p in perfis:
        tags = " ".join(f'<span class="chip">{esc(t[0] if isinstance(t,(list,tuple)) else t)}</span>'
                        for t in (p.get("top_hashtags") or [])[:6])
        cards += (f'<div class="card"><div class="c-head"><b>@{esc(p.get("handle"))}</b>'
                  f'<span class="c-sub">{bi(p.get("seguidores"))} seg · mediana {bi((p.get("views") or {}).get("mediana"))} views</span></div>'
                  f'<p class="bio">{esc(p.get("bio") or "—")}</p><div class="chips">{tags}</div></div>')

    render(saida, titulo, len(perfis), ths, rows, cards)

def render(saida, titulo, n, ths, rows, cards):
    CSS = r"""
:root{--paper:#FBFAF7;--surface:#FFF;--ink:#1B1E23;--ink-soft:#4A5057;--muted:#8A9099;--line:#E7E3DB;--teal:#0F766E;--teal-soft:#E7F0EE;--ochre:#B4712A;
--serif:ui-serif,"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;--sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;--mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;}
@media (prefers-color-scheme:dark){:root{--paper:#121417;--surface:#191C21;--ink:#ECEEF0;--ink-soft:#B3B8BF;--muted:#7C838C;--line:#2A2E35;--teal:#3FB8A6;--teal-soft:#12312D;--ochre:#D69A54;}}
:root[data-theme=dark]{--paper:#121417;--surface:#191C21;--ink:#ECEEF0;--ink-soft:#B3B8BF;--muted:#7C838C;--line:#2A2E35;--teal:#3FB8A6;--teal-soft:#12312D;--ochre:#D69A54;}
:root[data-theme=light]{--paper:#FBFAF7;--surface:#FFF;--ink:#1B1E23;--ink-soft:#4A5057;--muted:#8A9099;--line:#E7E3DB;--teal:#0F766E;--teal-soft:#E7F0EE;--ochre:#B4712A;}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.5}
.wrap{max-width:1000px;margin:0 auto;padding:0 22px 48px}
.top{border-bottom:1px solid var(--line);background:var(--surface)}.top-in{max-width:1000px;margin:0 auto;padding:26px 22px}
.brand{font-family:var(--mono);font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-soft);display:flex;align-items:center;gap:9px}
.brand .dot{width:9px;height:9px;border-radius:50%;background:var(--teal)}
h1{font-family:var(--serif);font-weight:600;font-size:1.7rem;margin:8px 0 2px}.sub{color:var(--ink-soft)}
h2{font-family:var(--serif);font-weight:600;font-size:1.15rem;margin:30px 0 12px}
.tbl-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin-top:18px}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th,td{padding:11px 13px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}
th{font-family:var(--mono);font-size:.66rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:0}
.who b{display:block}.nome{color:var(--muted);font-size:.8rem}
td.lead{color:var(--teal);font-weight:600;background:var(--teal-soft)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-top:14px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.c-head b{font-size:1rem}.c-sub{display:block;font-family:var(--mono);font-size:.72rem;color:var(--muted);margin-top:2px}
.bio{color:var(--ink-soft);font-size:.9rem;margin:10px 0}.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{background:var(--teal-soft);color:var(--teal);border-radius:999px;padding:3px 9px;font-family:var(--mono);font-size:.72rem}
.foot{max-width:1000px;margin:0 auto;padding:20px 22px;color:var(--muted);font-size:.78rem}
.note{color:var(--ink-soft);font-size:.9rem;margin-top:8px}
.toggle{position:fixed;top:14px;right:14px;background:var(--surface);border:1px solid var(--line);color:var(--ink-soft);border-radius:999px;padding:6px 11px;font-family:var(--mono);font-size:.72rem;cursor:pointer}
@media print{.toggle{display:none}}
"""
    JS = ("(function(){var b=document.getElementById('tg');if(!b)return;b.onclick=function(){var r=document.documentElement,"
          "d=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');"
          "r.setAttribute('data-theme',d==='dark'?'light':'dark');};})();")
    doc = f"""<!doctype html><html lang=pt-BR><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1"><title>Mapa do nicho — {esc(titulo)}</title>
<style>{CSS}</style></head><body>
<button class=toggle id=tg>◑ Tema</button>
<header class=top><div class=top-in>
<div class=brand><span class=dot></span> FullBPO · Mapa Competitivo</div>
<h1>{esc(titulo)}</h1><div class=sub>{n} perfis comparados · posicionamento · tração</div>
</div></header>
<main class=wrap>
<h2>Tração — lado a lado</h2>
<div class=tbl-wrap><table><thead><tr><th>Creator</th>{ths}</tr></thead><tbody>{rows}</tbody></table></div>
<p class=note>Célula em <span style="color:var(--teal)"><b>destaque</b></span> = líder da coluna. Views por mediana (alcance típico); "melhor vídeo" mostra o teto de cada um.</p>
<h2>Posicionamento</h2>
<div class=cards>{cards}</div>
</main>
<footer class=foot>FullBPO — Backoffice Inteligente · dados públicos via Apify (estimativas de mercado) · uso interno.</footer>
<script>{JS}</script></body></html>"""
    open(saida, "w", encoding="utf-8").write(doc)
    print(f"mapa gerado: {saida} — {n} perfis")

if __name__ == "__main__":
    main()
