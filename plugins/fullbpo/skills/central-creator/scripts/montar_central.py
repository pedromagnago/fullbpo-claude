#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# montar_central.py — a CENTRAL do creator: junta todas as entregas
# (estratégia/Shop, dossiês, estudo de vídeo frame a frame, performance,
# painel de vendas) em UM ÚNICO HTML com abas. Cada peça é embutida isolada
# em <iframe srcdoc> — mantém o CSS/tema/JS de cada uma sem colisão — e o
# toggle de tema da Central propaga pra todas.
#
# Uso: montar_central.py <central.json> [saida.html]
#
# central.json:
# {
#   "cliente": "Nome", "subtitulo": "@handle · Divisão Shop", "data": "DD/MM/AAAA",
#   "resumo": "1 linha do que é isto (opcional)",
#   "tabs": [
#     {"id":"visao","label":"Visão geral","tipo":"embed","src":"visao.html"},
#     {"id":"shop","label":"Estratégia · Shop","tipo":"embed","src":"shop.html"},
#     {"id":"vendas","label":"Vendas","tipo":"embed","src":"painel.html","badge":"modelo","nota":"Ativa com o CSV do Affiliate."},
#     {"id":"tt","label":"Abrir no TikTok","tipo":"link","href":"https://..."}
#   ]
# }
# Caminhos "src" são relativos à pasta do central.json.
# ---------------------------------------------------------------------------
import sys, os, json, html, re

def esc(s): return html.escape(str(s if s is not None else ""), quote=True)

def esc_srcdoc(doc):
    # conteúdo de um atributo HTML entre aspas duplas: basta & e "
    return doc.replace("&", "&amp;").replace('"', "&quot;")

# o toggle de tema de cada peça (.toggle, convenção FullBPO) é escondido — a
# Central controla o tema de todas via postMessage.
LISTENER = ("<style>.toggle{display:none!important}</style>"
            "<script>window.addEventListener('message',function(e){if(e&&e.data&&e.data.fullbpo_tema){"
            "document.documentElement.setAttribute('data-theme',e.data.fullbpo_tema);}});</script>")

def inject_listener(doc):
    # injeta o listener de tema antes do </body> (ou no fim)
    if re.search(r"</body>", doc, re.I):
        return re.sub(r"</body>", LISTENER + "</body>", doc, count=1, flags=re.I)
    return doc + LISTENER

def carregar(base, src):
    p = src if os.path.isabs(src) else os.path.join(base, src)
    with open(p, encoding="utf-8") as f:
        return f.read()

def main():
    if len(sys.argv) < 2:
        print("uso: montar_central.py <central.json> [saida.html]", file=sys.stderr); sys.exit(2)
    manifesto = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else "central.html"
    d = json.load(open(manifesto, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(manifesto))

    tabs = d.get("tabs", [])
    btns = ""; panels = ""
    for i, t in enumerate(tabs):
        tid = t.get("id") or f"t{i}"
        ativo = " ativo" if i == 0 else ""
        badge = f'<span class=tab-badge>{esc(t.get("badge"))}</span>' if t.get("badge") else ""
        if t.get("tipo") == "link" and t.get("href"):
            btns += (f'<a class="tab" href="{esc(t["href"])}" target="_blank" rel="noopener">'
                     f'{esc(t.get("label"))} ↗</a>')
            continue
        btns += (f'<button class="tab{ativo}" data-tab="{esc(tid)}">{esc(t.get("label"))}{badge}</button>')
        nota = f'<div class=panel-nota>{esc(t.get("nota"))}</div>' if t.get("nota") else ""
        try:
            doc = inject_listener(carregar(base, t.get("src", "")))
            body = f'<iframe title="{esc(t.get("label"))}" srcdoc="{esc_srcdoc(doc)}" loading="lazy"></iframe>'
        except (OSError, ValueError) as e:
            body = f'<div class=erro>Não foi possível carregar <code>{esc(t.get("src"))}</code> ({esc(e)}).</div>'
        panels += f'<section class="panel{ativo}" id="p-{esc(tid)}">{nota}{body}</section>'

    CSS = r"""
:root{--paper:#FBFAF7;--surface:#FFF;--ink:#1B1E23;--ink-soft:#4A5057;--muted:#8A9099;--line:#E7E3DB;--teal:#0F766E;--teal-soft:#E7F0EE;--ochre:#B4712A;--shadow:0 1px 2px rgba(20,22,27,.05),0 6px 18px rgba(20,22,27,.07);--serif:ui-serif,"Iowan Old Style",Palatino,Georgia,serif;--sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;--mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;}
@media (prefers-color-scheme:dark){:root{--paper:#0F1113;--surface:#191C21;--ink:#ECEEF0;--ink-soft:#B3B8BF;--muted:#7C838C;--line:#2A2E35;--teal:#3FB8A6;--teal-soft:#12312D;--ochre:#D69A54;}}
:root[data-theme=dark]{--paper:#0F1113;--surface:#191C21;--ink:#ECEEF0;--ink-soft:#B3B8BF;--muted:#7C838C;--line:#2A2E35;--teal:#3FB8A6;--teal-soft:#12312D;--ochre:#D69A54;}
:root[data-theme=light]{--paper:#FBFAF7;--surface:#FFF;--ink:#1B1E23;--ink-soft:#4A5057;--muted:#8A9099;--line:#E7E3DB;--teal:#0F766E;--teal-soft:#E7F0EE;--ochre:#B4712A;}
*{box-sizing:border-box}html,body{height:100%}body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);display:flex;flex-direction:column;overflow:hidden}
.top{background:var(--surface);border-bottom:1px solid var(--line);padding:12px 20px 0;flex:0 0 auto}
.top-row{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.brand{font-family:var(--mono);font-size:.7rem;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-soft);display:flex;align-items:center;gap:8px}
.brand .dot{width:8px;height:8px;border-radius:50%;background:var(--teal)}
.cliente{font-family:var(--serif);font-size:1.15rem;font-weight:600}
.meta{color:var(--muted);font-size:.82rem}
.tabbar{display:flex;gap:4px;margin-top:11px;overflow-x:auto;scrollbar-width:thin}
.tab{appearance:none;background:transparent;border:0;border-bottom:2px solid transparent;color:var(--ink-soft);font-family:var(--sans);font-size:.9rem;padding:9px 14px;cursor:pointer;white-space:nowrap;display:inline-flex;align-items:center;gap:7px;text-decoration:none;border-radius:8px 8px 0 0}
.tab:hover{color:var(--ink);background:var(--paper)}
.tab.ativo{color:var(--teal);border-bottom-color:var(--teal);font-weight:600}
.tab-badge{font-family:var(--mono);font-size:.58rem;letter-spacing:.05em;text-transform:uppercase;background:var(--ochre);color:#fff;border-radius:5px;padding:1px 6px}
.stage{flex:1 1 auto;position:relative;min-height:0}
.panel{position:absolute;inset:0;display:none;flex-direction:column}
.panel.ativo{display:flex}
.panel-nota{flex:0 0 auto;background:var(--teal-soft);color:var(--teal);font-size:.82rem;padding:8px 20px;border-bottom:1px solid var(--line)}
.panel iframe{flex:1 1 auto;width:100%;height:100%;border:0;background:var(--paper)}
.erro{padding:30px;color:var(--muted);font-family:var(--mono);font-size:.85rem}
.toggle{position:fixed;top:11px;right:16px;z-index:20;background:var(--surface);border:1px solid var(--line);color:var(--ink-soft);border-radius:999px;padding:6px 11px;font-family:var(--mono);font-size:.72rem;cursor:pointer;box-shadow:var(--shadow)}
"""
    JS = r"""
(function(){
  var tabs=document.querySelectorAll('.tab[data-tab]'),panels=document.querySelectorAll('.panel');
  tabs.forEach(function(b){b.addEventListener('click',function(){
    tabs.forEach(function(x){x.classList.remove('ativo')});
    panels.forEach(function(p){p.classList.remove('ativo')});
    b.classList.add('ativo');
    var p=document.getElementById('p-'+b.getAttribute('data-tab'));
    if(p)p.classList.add('ativo');
  });});
  function irPara(id){var b=document.querySelector('.tab[data-tab="'+id+'"]');if(b)b.click();}
  window.addEventListener('message',function(e){if(e&&e.data&&e.data.fullbpo_goto){irPara(e.data.fullbpo_goto);
    try{window.scrollTo(0,0);}catch(_){}}});
  var tg=document.getElementById('tg');
  if(tg)tg.addEventListener('click',function(){
    var r=document.documentElement;
    var cur=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
    var n=cur==='dark'?'light':'dark';
    r.setAttribute('data-theme',n);
    document.querySelectorAll('.panel iframe').forEach(function(f){try{f.contentWindow.postMessage({fullbpo_tema:n},'*');}catch(e){}});
  });
})();
"""
    resumo = f'<div class=meta>{esc(d.get("resumo"))}</div>' if d.get("resumo") else ""
    doc = f"""<!doctype html><html lang=pt-BR><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Central — {esc(d.get("cliente"))}</title><style>{CSS}</style></head><body>
<button class=toggle id=tg>◑ Tema</button>
<header class=top>
  <div class=top-row>
    <span class=brand><span class=dot></span> FullBPO · Central de Inteligência</span>
    <span class=cliente>{esc(d.get("cliente"))}</span>
    <span class=meta>{esc(d.get("subtitulo"))}{(" · " + esc(d.get("data"))) if d.get("data") else ""}</span>
  </div>
  {resumo}
  <nav class=tabbar>{btns}</nav>
</header>
<div class=stage>{panels}</div>
<script>{JS}</script>
</body></html>"""
    open(saida, "w", encoding="utf-8").write(doc)
    print(f"central gerada: {saida} ({os.path.getsize(saida)//1024} KB)")

if __name__ == "__main__":
    main()
