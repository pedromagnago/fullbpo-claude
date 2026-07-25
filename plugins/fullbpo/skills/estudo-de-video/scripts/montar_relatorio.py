#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# montar_relatorio.py — monta o relatório HTML padrão da FullBPO (estudo de
# vídeo + perfil) a partir de um conteudo.json + a pasta de frames.
#
# Uso:
#   python3 montar_relatorio.py <conteudo.json> [saida.html]
#
# O HTML é AUTOCONTIDO: CSS inline e imagens embutidas em base64 (data URI),
# então é um único arquivo que o cliente abre em qualquer navegador ou
# imprime em PDF. Tema claro/escuro automático. Sem dependências externas.
#
# Esquema do conteudo.json: veja SKILL.md (estudo-de-video).
# ---------------------------------------------------------------------------
import sys, os, json, base64, html, mimetypes

def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)

def rich(s):
    # escapa e aplica **negrito** e *itálico*
    s = esc(s)
    out, bold = [], False
    for seg in s.split("**"):
        parts, it = [], False
        for sub in seg.split("*"):
            parts.append(f"<em>{sub}</em>" if it else sub); it = not it
        seg = "".join(parts)
        out.append(f"<strong>{seg}</strong>" if bold else seg); bold = not bold
    return "".join(out)

def paras(v):
    if not v: return ""
    if isinstance(v, str): v = [v]
    return "".join(f"<p>{rich(p)}</p>" for p in v)

def data_uri(path):
    try:
        mime = mimetypes.guess_type(path)[0] or "image/jpeg"
        with open(path, "rb") as f:
            return f"data:{mime};base64," + base64.b64encode(f.read()).decode()
    except Exception:
        return ""

def main():
    if len(sys.argv) < 2:
        print("uso: montar_relatorio.py <conteudo.json> [saida.html]", file=sys.stderr); sys.exit(2)
    cj = json.load(open(sys.argv[1], encoding="utf-8"))
    out_path = sys.argv[2] if len(sys.argv) > 2 else "relatorio.html"
    frames_dir = cj.get("frames_dir", "")

    obj = cj.get("objeto", {})
    stats = obj.get("video_stats", {})
    perfil = cj.get("perfil", {})
    video = cj.get("video", {})

    # --- meta (cabeçalho) ---
    meta_rows = [
        ("Cliente", cj.get("cliente", "—")),
        ("Data do estudo", cj.get("data", "—")),
        ("Objeto", f'{esc(obj.get("autora",""))} · {esc(obj.get("handle",""))}'),
        ("Analista", cj.get("analista", "FullBPO")),
    ]
    meta_html = "".join(
        f'<div class="meta-item"><span class="meta-k">{esc(k)}</span>'
        f'<span class="meta-v">{v if k=="Objeto" else esc(v)}</span></div>'
        for k, v in meta_rows)

    links = []
    if obj.get("video_url"):  links.append(f'<a href="{esc(obj["video_url"])}">Vídeo analisado ↗</a>')
    if obj.get("perfil_url"): links.append(f'<a href="{esc(obj["perfil_url"])}">Perfil ↗</a>')
    links_html = f'<div class="links">{" · ".join(links)}</div>' if links else ""

    # --- perfil: tiles ---
    tiles = "".join(
        f'<div class="tile"><div class="tile-v">{esc(m.get("valor"))}</div>'
        f'<div class="tile-k">{esc(m.get("rotulo"))}</div>'
        + (f'<div class="tile-n">{esc(m.get("nota"))}</div>' if m.get("nota") else "")
        + "</div>"
        for m in perfil.get("metricas", []))

    chips = "".join(
        f'<span class="chip">{esc(t[0] if isinstance(t,(list,tuple)) else t)}'
        + (f'<span class="chip-n">{esc(t[1])}</span>' if isinstance(t,(list,tuple)) and len(t)>1 else "")
        + "</span>"
        for t in perfil.get("hashtags", []))

    tops = ""
    for i, v in enumerate(perfil.get("top_videos", []), 1):
        tops += (
            f'<li><span class="rank">{i:02d}</span>'
            f'<span class="top-title">{esc(v.get("titulo"))}</span>'
            f'<span class="top-stats"><b>{esc(v.get("views"))}</b> views · {esc(v.get("likes"))} likes'
            + (f' · {esc(v.get("data"))}' if v.get("data") else "") + "</span></li>")

    perfil_html = ""
    if perfil:
        perfil_html = f"""
      <section class="sec">
        <div class="sec-head"><span class="eyebrow">01 · Perfil</span>
          <h2>Quem é {esc(obj.get("autora","o perfil"))}</h2></div>
        {f'<div class="tiles">{tiles}</div>' if tiles else ''}
        <div class="lead2">{paras(perfil.get("leitura"))}</div>
        <div class="two-col">
          {f'<div class="panel"><h3>Hashtags recorrentes</h3><div class="chips">{chips}</div></div>' if chips else ''}
          {f'<div class="panel"><h3>Vídeos de maior alcance</h3><ol class="tops">{tops}</ol></div>' if tops else ''}
        </div>
      </section>"""

    # --- vídeo: barra de stats ---
    vstat_map = [("views","Views"),("likes","Likes"),("comentarios","Comentários"),
                 ("compart","Compart."),("salvos","Salvos"),("duracao","Duração"),
                 ("publicado","Publicado")]
    vstats = "".join(
        f'<div class="vstat"><span class="vstat-v">{esc(stats.get(k))}</span>'
        f'<span class="vstat-k">{esc(lbl)}</span></div>'
        for k, lbl in vstat_map if stats.get(k) not in (None, ""))

    # --- linha do tempo ---
    tl = ""
    for row in video.get("timeline", []):
        img = ""
        if row.get("frame") and frames_dir:
            uri = data_uri(os.path.join(frames_dir, row["frame"]))
            if uri:
                img = f'<div class="tl-img"><img src="{uri}" alt="Frame em {esc(row.get("t"))}" loading="lazy"></div>'
        fala = f'<blockquote>{rich(row.get("fala"))}</blockquote>' if row.get("fala") else ""
        tl += f"""
        <div class="tl-row{' has-img' if img else ''}">
          {img}
          <div class="tl-body">
            <span class="tl-time">{esc(row.get("t"))}</span>
            <div class="tl-tela">{rich(row.get("tela"))}</div>
            {fala}
          </div>
        </div>"""

    gancho = f'<div class="panel"><h3>Gancho</h3>{paras(video.get("gancho"))}</div>' if video.get("gancho") else ""
    estrut = f'<div class="panel"><h3>Estrutura</h3>{paras(video.get("estrutura"))}</div>' if video.get("estrutura") else ""
    ge = f'<div class="two-col">{gancho}{estrut}</div>' if (gancho or estrut) else ""

    video_html = ""
    if video:
        video_html = f"""
      <section class="sec">
        <div class="sec-head"><span class="eyebrow">02 · Vídeo</span>
          <h2>Anatomia do vídeo</h2></div>
        {f'<div class="vstats">{vstats}</div>' if vstats else ''}
        {ge}
        {f'<h3 class="tl-h">Linha do tempo — frame a frame</h3><div class="timeline">{tl}</div>' if tl else ''}
      </section>"""

    # --- insights ---
    ins = ""
    for i, it in enumerate(cj.get("insights", []), 1):
        if isinstance(it, dict):
            ins += f'<div class="insight"><span class="i-num">{i:02d}</span><h3>{rich(it.get("titulo"))}</h3>{paras(it.get("texto"))}</div>'
        else:
            ins += f'<div class="insight"><span class="i-num">{i:02d}</span>{paras(it)}</div>'
    insights_html = f"""
      <section class="sec">
        <div class="sec-head"><span class="eyebrow">03 · Recomendações</span>
          <h2>O que fazer com isso</h2></div>
        <div class="insights">{ins}</div>
      </section>""" if ins else ""

    resumo_html = f"""
      <section class="sec lead-sec">
        <div class="sec-head"><span class="eyebrow">Resumo executivo</span></div>
        <div class="lead">{paras(cj.get("resumo_executivo"))}</div>
      </section>""" if cj.get("resumo_executivo") else ""

    metod = cj.get("metodologia", "")

    return_html(out_path, cj, obj, meta_html, links_html, resumo_html,
                perfil_html, video_html, insights_html, metod)

def return_html(out_path, cj, obj, meta_html, links_html, resumo_html,
                perfil_html, video_html, insights_html, metod):
    titulo = f'Estudo de Vídeo — {obj.get("autora","")}'.strip(" —")
    CSS = r"""
:root{
  --paper:#FBFAF7; --surface:#FFFFFF; --ink:#1B1E23; --ink-soft:#4A5057;
  --muted:#8A9099; --line:#E7E3DB; --teal:#0F766E; --teal-soft:#E7F0EE;
  --ochre:#B4712A; --ochre-soft:#F6ECDC; --shadow:0 1px 2px rgba(20,22,27,.04),0 8px 24px rgba(20,22,27,.06);
  --serif:ui-serif,"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono","Cascadia Code","Roboto Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --paper:#121417; --surface:#191C21; --ink:#ECEEF0; --ink-soft:#B3B8BF;
  --muted:#7C838C; --line:#2A2E35; --teal:#3FB8A6; --teal-soft:#12312D;
  --ochre:#D69A54; --ochre-soft:#2A2114; --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
}}
:root[data-theme="light"]{
  --paper:#FBFAF7; --surface:#FFFFFF; --ink:#1B1E23; --ink-soft:#4A5057;
  --muted:#8A9099; --line:#E7E3DB; --teal:#0F766E; --teal-soft:#E7F0EE;
  --ochre:#B4712A; --ochre-soft:#F6ECDC; --shadow:0 1px 2px rgba(20,22,27,.04),0 8px 24px rgba(20,22,27,.06);
}
:root[data-theme="dark"]{
  --paper:#121417; --surface:#191C21; --ink:#ECEEF0; --ink-soft:#B3B8BF;
  --muted:#7C838C; --line:#2A2E35; --teal:#3FB8A6; --teal-soft:#12312D;
  --ochre:#D69A54; --ochre-soft:#2A2114; --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:960px;margin:0 auto;padding:0 24px}
p{margin:0 0 .8em} p:last-child{margin-bottom:0}
a{color:var(--teal);text-decoration:none;border-bottom:1px solid transparent}
a:hover{border-bottom-color:var(--teal)}
h2,h3{font-family:var(--serif);font-weight:600;letter-spacing:-.01em;text-wrap:balance;margin:0}
h2{font-size:1.9rem;line-height:1.15} h3{font-size:1.12rem;margin-bottom:.5em}
.eyebrow{font-family:var(--mono);font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--teal)}
/* masthead */
.mast{border-bottom:1px solid var(--line);background:var(--surface)}
.mast-in{max-width:960px;margin:0 auto;padding:34px 24px 30px}
.brand{display:flex;align-items:center;gap:10px;font-family:var(--mono);font-size:.8rem;
  letter-spacing:.18em;text-transform:uppercase;color:var(--ink-soft)}
.brand .dot{width:9px;height:9px;border-radius:50%;background:var(--teal)}
.mast h1{font-family:var(--serif);font-weight:600;letter-spacing:-.02em;font-size:2.5rem;
  line-height:1.08;margin:.5em 0 .1em;text-wrap:balance}
.mast .sub{color:var(--ink-soft);font-size:1.05rem;max-width:60ch}
.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-top:24px}
.meta-item{background:var(--surface);padding:12px 16px;display:flex;flex-direction:column;gap:3px}
.meta-k{font-family:var(--mono);font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.meta-v{font-size:.95rem;color:var(--ink)}
.links{margin-top:14px;font-family:var(--mono);font-size:.82rem}
/* sections */
main{padding:8px 0 40px}
.sec{padding:40px 0;border-bottom:1px solid var(--line)}
.sec:last-child{border-bottom:0}
.sec-head{margin-bottom:22px}
.sec-head h2{margin-top:.25em}
.lead-sec .lead{font-family:var(--serif);font-size:1.28rem;line-height:1.5;color:var(--ink);max-width:66ch}
.lead2{max-width:68ch;color:var(--ink-soft);margin-bottom:8px}
.lead2 p{margin-bottom:.7em}
/* tiles */
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin-bottom:26px}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px;box-shadow:var(--shadow)}
.tile-v{font-family:var(--mono);font-size:1.7rem;font-weight:600;letter-spacing:-.02em;
  color:var(--ink);font-variant-numeric:tabular-nums}
.tile-k{font-size:.8rem;color:var(--ink-soft);margin-top:2px}
.tile-n{font-family:var(--mono);font-size:.7rem;color:var(--muted);margin-top:4px}
/* two-col panels */
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:20px 22px;box-shadow:var(--shadow)}
.panel h3{color:var(--ink)}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{display:inline-flex;align-items:center;gap:6px;background:var(--teal-soft);color:var(--teal);
  border-radius:999px;padding:5px 12px;font-family:var(--mono);font-size:.8rem}
.chip-n{opacity:.65;font-size:.72rem}
.tops{list-style:none;margin:0;padding:0;counter-reset:none}
.tops li{display:grid;grid-template-columns:auto 1fr;grid-template-rows:auto auto;
  column-gap:12px;padding:10px 0;border-top:1px solid var(--line)}
.tops li:first-child{border-top:0}
.rank{grid-row:1/3;font-family:var(--mono);font-size:.95rem;color:var(--ochre);align-self:center}
.top-title{font-size:.9rem;line-height:1.35}
.top-stats{font-family:var(--mono);font-size:.74rem;color:var(--muted);font-variant-numeric:tabular-nums}
.top-stats b{color:var(--ink-soft);font-weight:600}
/* video stats bar */
.vstats{display:grid;grid-template-columns:repeat(auto-fit,minmax(96px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-bottom:26px}
.vstat{background:var(--surface);padding:14px 12px;text-align:center}
.vstat-v{display:block;font-family:var(--mono);font-size:1.15rem;font-weight:600;color:var(--ink);font-variant-numeric:tabular-nums}
.vstat-k{display:block;font-size:.72rem;color:var(--muted);margin-top:3px}
/* timeline */
.tl-h{margin:28px 0 16px}
.timeline{display:flex;flex-direction:column;gap:14px}
.tl-row{background:var(--surface);border:1px solid var(--line);border-radius:14px;
  padding:16px 18px;box-shadow:var(--shadow)}
.tl-row.has-img{display:grid;grid-template-columns:300px 1fr;gap:20px;align-items:start}
.tl-img{border-radius:10px;overflow:hidden;border:1px solid var(--line);background:#000;line-height:0}
.tl-img img{width:100%;height:auto;display:block}
.tl-time{display:inline-block;font-family:var(--mono);font-size:.74rem;letter-spacing:.04em;
  color:var(--teal);background:var(--teal-soft);border-radius:6px;padding:3px 9px;margin-bottom:8px}
.tl-tela{font-weight:600;color:var(--ink);margin-bottom:8px;line-height:1.45}
.tl-body blockquote{margin:0;padding-left:14px;border-left:2px solid var(--ochre);
  font-family:var(--serif);font-style:italic;font-size:1.02rem;color:var(--ink-soft)}
/* insights */
.insights{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.insight{background:var(--surface);border:1px solid var(--line);border-radius:14px;
  padding:20px 22px;box-shadow:var(--shadow);position:relative}
.insight .i-num{font-family:var(--mono);font-size:.8rem;color:var(--ochre)}
.insight h3{color:var(--ink);margin:.3em 0 .4em}
.insight p{color:var(--ink-soft);font-size:.95rem}
/* footer */
.foot{border-top:1px solid var(--line);background:var(--surface)}
.foot-in{max-width:960px;margin:0 auto;padding:26px 24px 40px;color:var(--muted);font-size:.82rem}
.foot .sig{font-family:var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--ink-soft);margin-bottom:8px}
.foot .metod{max-width:80ch}
/* theme toggle */
.toggle{position:fixed;top:16px;right:16px;z-index:10;background:var(--surface);
  border:1px solid var(--line);color:var(--ink-soft);border-radius:999px;padding:7px 12px;
  font-family:var(--mono);font-size:.72rem;cursor:pointer;box-shadow:var(--shadow)}
.toggle:hover{color:var(--teal)}
:focus-visible{outline:2px solid var(--teal);outline-offset:2px;border-radius:4px}
@media (max-width:720px){
  .mast h1{font-size:1.9rem} h2{font-size:1.55rem}
  .two-col,.insights{grid-template-columns:1fr}
  .tl-row.has-img{grid-template-columns:1fr}
  .tl-img{max-width:340px}
}
@media print{
  .toggle{display:none} body{background:#fff;color:#000}
  .tl-row,.tile,.panel,.insight,.sec{break-inside:avoid;box-shadow:none}
  .mast,.foot,.tile,.panel,.tl-row,.insight{background:#fff}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""
    JS = ("(function(){var b=document.getElementById('tg');if(!b)return;"
          "b.addEventListener('click',function(){var r=document.documentElement;"
          "var d=(r.getAttribute('data-theme')|| (matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'));"
          "var n=d==='dark'?'light':'dark';r.setAttribute('data-theme',n);"
          "b.textContent=n==='dark'?'\\u25D0 Tema':'\\u25D1 Tema';});})();")

    doc = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title>
<style>{CSS}</style>
</head>
<body>
<button class="toggle" id="tg" aria-label="Alternar tema">◑ Tema</button>
<header class="mast">
  <div class="mast-in">
    <div class="brand"><span class="dot"></span> FullBPO · Backoffice Inteligente</div>
    <h1>Estudo de Vídeo &amp; Perfil</h1>
    <div class="sub">Análise de conteúdo de referência — o que funciona, por quê, e como aplicar.</div>
    <div class="meta">{meta_html}</div>
    {links_html}
  </div>
</header>
<main class="wrap">
  {resumo_html}
  {perfil_html}
  {video_html}
  {insights_html}
</main>
<footer class="foot">
  <div class="foot-in">
    <div class="sig">FullBPO — Backoffice Inteligente</div>
    <div class="metod">{rich(metod)}</div>
    <p style="margin-top:12px">Documento confidencial, preparado para o cliente indicado. Conteúdo analisado é público e de titularidade de seus respectivos autores; este estudo é material de curadoria e inteligência, não republicação.</p>
  </div>
</footer>
<script>{JS}</script>
</body>
</html>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"relatório gerado: {out_path} ({os.path.getsize(out_path)//1024} KB)")

if __name__ == "__main__":
    main()
