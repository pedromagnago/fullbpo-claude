#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# montar_referencias.py — "Referências decodificadas": teardown COMPARATIVO de
# vários vídeos virais do nicho (ao contrário do montar_relatorio.py, que é 1
# vídeo a fundo). Para cada vídeo mostra o gancho (frame + fala dos ~3s), o
# arquétipo, o dispositivo visual, a estrutura e "o que o cliente copia" — e
# fecha com o PADRÃO comum + um roteiro-modelo. HTML autocontido (frames em
# base64), tema FullBPO, integra com a central-creator (tema via postMessage).
#
# Uso:
#   python3 montar_referencias.py <referencias.json> [saida.html]
# ---------------------------------------------------------------------------
import sys, os, json, base64, html, mimetypes

def esc(s): return html.escape(str(s if s is not None else ""), quote=True)
def brnum(n):
    try: return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError): return str(n)

def datauri(path):
    if not path or not os.path.exists(path): return ""
    mt = mimetypes.guess_type(path)[0] or "image/jpeg"
    return f"data:{mt};base64," + base64.b64encode(open(path, "rb").read()).decode()

def main():
    if len(sys.argv) < 2:
        print("uso: montar_referencias.py <referencias.json> [saida.html]"); sys.exit(2)
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2] if len(sys.argv) > 2 else "referencias.html"
    base = os.path.dirname(os.path.abspath(sys.argv[1]))

    cards = ""
    for v in d.get("videos", []):
        frames = ""
        for fr in v.get("frames", [])[:2]:
            p = fr if os.path.isabs(fr) else os.path.join(base, fr)
            uri = datauri(p)
            if uri: frames += f'<img src="{uri}" alt="frame do vídeo" loading="lazy">'
        estr = "".join(f'<li>{esc(x)}</li>' for x in v.get("estrutura", []))
        copiar = "".join(f'<li>{esc(x)}</li>' for x in v.get("copiar", []))
        stats = f'{brnum(v.get("views"))} views · {brnum(v.get("seguidores"))} seg'
        link = v.get("url")
        titulo = f'@{esc(v.get("handle"))}'
        if link: titulo = f'<a href="{esc(link)}" target="_blank" rel="noopener">{titulo}</a>'
        cards += f"""<article class="ref">
<div class="ref-media">{frames}<span class="arq">{esc(v.get("arquetipo",""))}</span></div>
<div class="ref-body">
<div class="ref-head"><h3>{titulo}</h3><span class="stat">{esc(stats)}</span></div>
<div class="gancho"><span class="g-k">Gancho (0–3s)</span><p>"{esc(v.get("gancho",""))}"</p></div>
<div class="disp"><span class="g-k">Dispositivo visual</span><p>{esc(v.get("dispositivo",""))}</p></div>
<div class="cols">
<div><span class="g-k">Estrutura</span><ol class="beats">{estr}</ol></div>
<div class="copy"><span class="g-k">O que a {esc(d.get("cliente_curto","cliente"))} copia</span><ul class="chk">{copiar}</ul></div>
</div></div></article>"""

    s = d.get("sintese", {})
    padrao = "".join(f'<li>{esc(x)}</li>' for x in s.get("padrao", []))
    roteiro = "".join(
        f'<li><span class="rt-t">{esc(p.get("t"))}</span><span class="rt-d">{esc(p.get("o"))}</span></li>'
        for p in s.get("roteiro", []))
    evitar = "".join(f'<li>{esc(x)}</li>' for x in s.get("evitar", []))
    sint = f"""<section class="sint" id="padrao">
<div class="kick">o denominador comum</div><h2>{esc(s.get("titulo","O padrão que se repete"))}</h2>
<p>{esc(s.get("intro",""))}</p>
<div class="two"><div class="box hot"><div class="box-h">O que todo viral do nicho tem</div><ul class="chk big">{padrao}</ul></div>
<div class="box"><div class="box-h">O que a {esc(d.get("cliente_curto","cliente"))} faz e derruba o alcance</div><ul class="x">{evitar}</ul></div></div>
<div class="box roteiro"><div class="box-h">Roteiro-modelo do próximo vídeo (30–60s)</div><ol class="rot">{roteiro}</ol></div>
</section>"""

    render(out, d, cards, sint)

CSS = r"""
:root{--paper:#FBFAF7;--surface:#FFF;--ink:#1B1E23;--ink-soft:#4A5057;--muted:#8A9099;--line:#E7E3DB;
--teal:#0F766E;--teal-soft:#E7F0EE;--ochre:#B4712A;--ochre-soft:#F6ECDC;--red:#B4372A;
--shadow:0 1px 2px rgba(20,22,27,.04),0 8px 20px rgba(20,22,27,.06);
--serif:ui-serif,"Iowan Old Style",Palatino,Georgia,serif;--sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
--mono:ui-monospace,"SF Mono","Cascadia Code",Menlo,Consolas,monospace;}
@media (prefers-color-scheme:dark){:root{--paper:#0F1113;--surface:#191C21;--ink:#ECEEF0;--ink-soft:#B3B8BF;--muted:#7C838C;--line:#2A2E35;--teal:#3FB8A6;--teal-soft:#12312D;--ochre:#D69A54;--ochre-soft:#2A2114;--red:#E0705F;--shadow:0 1px 2px rgba(0,0,0,.3),0 10px 26px rgba(0,0,0,.35);}}
:root[data-theme=light]{--paper:#FBFAF7;--surface:#FFF;--ink:#1B1E23;--ink-soft:#4A5057;--muted:#8A9099;--line:#E7E3DB;--teal:#0F766E;--teal-soft:#E7F0EE;--ochre:#B4712A;--ochre-soft:#F6ECDC;--red:#B4372A;}
:root[data-theme=dark]{--paper:#0F1113;--surface:#191C21;--ink:#ECEEF0;--ink-soft:#B3B8BF;--muted:#7C838C;--line:#2A2E35;--teal:#3FB8A6;--teal-soft:#12312D;--ochre:#D69A54;--ochre-soft:#2A2114;--red:#E0705F;}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15.5px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:960px;margin:0 auto;padding:0 22px 64px}
h1,h2,h3{font-family:var(--serif);font-weight:600;letter-spacing:-.01em;margin:0}a{color:var(--teal)}
.top{border-bottom:1px solid var(--line);background:var(--surface)}
.top-in{max-width:960px;margin:0 auto;padding:26px 22px}
.brand{font-family:var(--mono);font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-soft);display:flex;align-items:center;gap:9px}
.brand .dot{width:9px;height:9px;border-radius:50%;background:var(--teal)}
.top h1{font-size:1.85rem;margin:10px 0 4px}.who{color:var(--ink-soft)}
.lead{max-width:960px;margin:0 auto;padding:18px 22px 0}.lead p{font-family:var(--serif);font-size:1.2rem;line-height:1.45;color:var(--ink-soft)}
.lead b{color:var(--ink)}
.refs{display:flex;flex-direction:column;gap:20px;margin-top:24px}
.ref{display:grid;grid-template-columns:220px 1fr;gap:20px;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:var(--shadow)}
.ref-media{position:relative;display:flex;flex-direction:column;gap:6px}
.ref-media img{width:100%;border-radius:10px;border:1px solid var(--line);display:block;aspect-ratio:9/16;object-fit:cover}
.arq{position:absolute;top:8px;left:8px;background:var(--ochre);color:#fff;font-family:var(--mono);font-size:.6rem;letter-spacing:.06em;text-transform:uppercase;padding:3px 8px;border-radius:6px}
.ref-head{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:10px}
.ref-head h3{font-size:1.15rem}.stat{font-family:var(--mono);font-size:.72rem;color:var(--muted);white-space:nowrap}
.g-k{font-family:var(--mono);font-size:.64rem;letter-spacing:.1em;text-transform:uppercase;color:var(--teal);display:block;margin-bottom:3px}
.gancho{background:var(--teal-soft);border-radius:10px;padding:10px 12px;margin-bottom:10px}
.gancho p{margin:0;font-size:1.02rem;color:var(--ink);font-family:var(--serif)}
.disp{margin-bottom:12px}.disp p{margin:0;color:var(--ink-soft);font-size:.92rem}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.beats{margin:0;padding-left:1.1em;color:var(--ink-soft);font-size:.88rem;line-height:1.7}
.chk,.x{margin:0;padding:0;list-style:none}
.chk li,.x li{padding:4px 0 4px 22px;position:relative;font-size:.9rem;color:var(--ink)}
.chk li:before{content:"✓";position:absolute;left:0;color:var(--teal);font-weight:700}
.x li:before{content:"✕";position:absolute;left:0;color:var(--red);font-weight:700}
.copy{background:var(--ochre-soft);border-radius:10px;padding:10px 12px}
.sint{margin-top:40px;border-top:2px solid var(--line);padding-top:28px}
.kick{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--teal);margin-bottom:6px}
.sint h2{font-size:1.5rem;margin-bottom:10px}.sint>p{color:var(--ink-soft)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:16px 0}
.box{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:var(--shadow)}
.box.hot{border-color:var(--ochre)}
.box-h{font-family:var(--mono);font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
.chk.big li{padding:7px 0 7px 24px;font-size:.95rem}
.roteiro{margin-top:4px}
.rot{margin:0;padding:0;counter-reset:r;list-style:none}
.rot li{display:flex;gap:14px;padding:10px 0;border-top:1px solid var(--line)}.rot li:first-child{border-top:0}
.rt-t{font-family:var(--mono);font-size:.8rem;color:var(--teal);flex:none;width:88px;font-weight:600}
.rt-d{color:var(--ink)}
.toggle{position:fixed;top:14px;right:14px;z-index:9;background:var(--surface);border:1px solid var(--line);color:var(--ink-soft);border-radius:999px;padding:6px 11px;font-family:var(--mono);font-size:.72rem;cursor:pointer;box-shadow:var(--shadow)}
.foot{max-width:960px;margin:0 auto;padding:24px 22px;color:var(--muted);font-size:.76rem;border-top:1px solid var(--line)}
:focus-visible{outline:2px solid var(--teal);outline-offset:2px}
@media (max-width:760px){.ref{grid-template-columns:1fr}.ref-media{max-width:200px}.cols,.two{grid-template-columns:1fr}.top h1{font-size:1.5rem}}
@media print{.toggle{display:none}body{background:#fff}.ref,.box{box-shadow:none;break-inside:avoid}}
"""

def render(out, d, cards, sint):
    JS = ("(function(){var b=document.getElementById('tg');if(b)b.onclick=function(){"
          "var r=document.documentElement,c=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');"
          "var n=c==='dark'?'light':'dark';r.setAttribute('data-theme',n);b.textContent=n==='dark'?'\\u25D0 Tema':'\\u25D1 Tema';};"
          "window.addEventListener('message',function(e){if(e&&e.data&&e.data.fullbpo_tema)"
          "document.documentElement.setAttribute('data-theme',e.data.fullbpo_tema);});})();")
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Referências decodificadas — {esc(d.get('cliente',''))}</title><style>{CSS}</style></head><body>
<button class="toggle" id="tg" aria-label="Alternar tema">◑ Tema</button>
<header class="top"><div class="top-in">
<div class="brand"><span class="dot"></span> FullBPO · Vídeos das referências decodificados</div>
<h1>O que faz o vídeo do concorrente estourar</h1>
<div class="who">{esc(d.get('subtitulo',''))}</div></div></header>
<div class="lead"><p>{esc(d.get('lead',''))}</p></div>
<main class="wrap"><div class="refs">{cards}</div>{sint}</main>
<footer class="foot">Gerado pela FullBPO — Backoffice Inteligente · vídeos públicos decodificados frame a frame (gancho, dispositivo, estrutura) para extrair o padrão replicável. Uso interno/cliente.</footer>
<script>{JS}</script></body></html>"""
    open(out, "w", encoding="utf-8").write(doc)
    print(f"referências geradas: {out} ({os.path.getsize(out)//1024} KB)")

if __name__ == "__main__":
    main()
