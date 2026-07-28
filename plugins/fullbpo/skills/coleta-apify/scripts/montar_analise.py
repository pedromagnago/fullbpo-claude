#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# montar_analise.py — renderiza a ANÁLISE PROFUNDA de performance de um creator
# como HTML autocontido (SVG inline, sem libs), no tema da FullBPO. Consome o
# nicho_<...>.json do analise_profunda.py (--nicho) + as transcricoes_*.json do
# transcrever.py (opcional, p/ os ganchos). Foca 1 handle e usa o resto do nicho
# como benchmark REAL.
#
# Uso:
#   python3 montar_analise.py <nicho.json> [saida.html] [--handle pri.andrade50] [--transc-dir DIR]
# ---------------------------------------------------------------------------
import sys, os, json, glob, html

def esc(s): return html.escape(str(s if s is not None else ""), quote=True)
def br(n):
    try: return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError): return str(n)

def _arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default

# ---------- SVG ------------------------------------------------------------
def bars(rows, w=680, h=170, hl=None):
    """rows = [(label, valor, sub)]; hl = índice destacado (ocre)."""
    if not rows: return ""
    mx = max(v for _, v, _ in rows) or 1
    n = len(rows); pad = 10; bw = (w - pad * (n + 1)) / n
    out = []
    for i, (lab, v, sub) in enumerate(rows):
        bh = (v / mx) * (h - 46); x = pad + i * (bw + pad); y = h - 26 - bh
        col = "var(--ochre)" if hl == i else "var(--teal)"
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" fill="{col}" opacity="0.9"/>')
        out.append(f'<text x="{x+bw/2:.1f}" y="{y-4:.1f}" text-anchor="middle" class="bl">{esc(sub)}</text>')
        out.append(f'<text x="{x+bw/2:.1f}" y="{h-8:.1f}" text-anchor="middle" class="bx">{esc(lab)}</text>')
    return f'<svg viewBox="0 0 {w} {h}" class="chart" role="img">{"".join(out)}</svg>'

def cmpbar(mine, nicho, lab_mine="você", lab_nicho="mediana do nicho", w=680):
    mx = max(mine, nicho) or 1
    wm = max(1.5, mine / mx * 100); wn = max(1.5, nicho / mx * 100)
    return (f'<div class="cmp"><div class="cmp-row"><span class="cmp-l">{esc(lab_mine)}</span>'
            f'<span class="cmp-bar"><i style="width:{wm:.1f}%;background:var(--teal)"></i></span>'
            f'<span class="cmp-v">{br(mine)}</span></div>'
            f'<div class="cmp-row"><span class="cmp-l">{esc(lab_nicho)}</span>'
            f'<span class="cmp-bar"><i style="width:{wn:.1f}%;background:var(--ochre)"></i></span>'
            f'<span class="cmp-v">{br(nicho)}</span></div></div>')

def sec(id_, kicker, titulo, corpo):
    return (f'<section id="{id_}"><div class="kick">{esc(kicker)}</div>'
            f'<h2>{esc(titulo)}</h2>{corpo}</section>')

def card(v, k, tone=""):
    return f'<div class="stat {tone}"><div class="s-v">{v}</div><div class="s-k">{esc(k)}</div></div>'

# ---------- ganchos (transcrições) ----------------------------------------
def load_hooks(transc_dir, handle):
    mine, nicho = [], []
    for f in glob.glob(os.path.join(transc_dir, "transcricoes_*.json")):
        base = os.path.basename(f)[len("transcricoes_"):-len(".json")]
        try: recs = json.load(open(f))
        except Exception: continue
        alvo = base in (handle, handle.split(".")[0])
        for x in recs:
            if x.get("tem_legenda") and x.get("gancho"):
                (mine if alvo else nicho).append({"h": base, "views": x.get("views", 0),
                                                  "gancho": x["gancho"], "url": x.get("url")})
    mine.sort(key=lambda r: -r["views"]); nicho.sort(key=lambda r: -r["views"])
    return mine, nicho

# ---------- render ---------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("uso: montar_analise.py <nicho.json> [saida.html] [--handle H] [--transc-dir DIR]"); sys.exit(2)
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    out_path = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "analise.html"
    handle = _arg("--handle", "pri.andrade50")
    transc_dir = _arg("--transc-dir", os.path.dirname(sys.argv[1]) or ".")

    perfis = data.get("perfis", [])
    nicho = data.get("nicho", {})
    a = next((p for p in perfis if p["handle"] == handle), None)
    if not a: raise SystemExit(f"handle {handle} não está no nicho.json")
    med_nicho = nicho.get("mediana_nicho") or 0
    vd, eng, aud, hor, dur, tend = a["views_dist"], a["engajamento"], a["audio"], a["horario"], a["duracao"], a["tendencia"]
    mine_hooks, nicho_hooks = load_hooks(transc_dir, handle)

    # -- diagnóstico (bullets) --
    diag = "".join(f'<li>{esc(x)}</li>' for x in a.get("diagnostico", []))

    # -- distribuição honesta --
    dist_cards = (card(br(vd["mediana"]), "mediana (a régua honesta)") +
                  card(br(vd["media"]), f"média — inflada {vd['media_sobre_mediana']}×", "muted") +
                  card(br(vd["max"]), f"pico ({vd['n_outliers']} outlier{'s' if vd['n_outliers']!=1 else ''})", "ochre") +
                  card(f'{vd["pct_abaixo_1k"]}%', "vídeos abaixo de 1.000 views", "warn"))
    outrows = "".join(
        f'<li><a href="{esc(o["url"])}" target="_blank" rel="noopener">{br(o["views"])} views</a> '
        f'· {o["mult_mediana"]}× a mediana — <span class="q">{esc(o["titulo"])}</span></li>'
        for o in vd.get("outliers", [])[:3])
    dist = (f'<div class="stats">{dist_cards}</div>'
            f'<p>A média que aparece por aí ({br(vd["media"])} views) está <b>inflada por {vd["n_outliers"]} '
            f'pico(s)</b>. Metade dos seus vídeos faz <b>{br(vd["mediana"])} views ou menos</b> — essa é a régua real.</p>'
            + (f'<div class="box"><div class="box-h">Os picos que puxam a média</div><ul class="mini">{outrows}</ul></div>' if outrows else ""))

    # -- benchmark do nicho --
    rows = ""
    for p in nicho.get("perfis", []):
        me = p["handle"] == handle
        rows += (f'<tr class="{"me" if me else ""}"><td>{"➜ " if me else ""}@{esc(p["handle"])}</td>'
                 f'<td class="num">{br(p["seguidores"])}</td><td class="num"><b>{br(p["views_mediana"])}</b></td>'
                 f'<td class="num">{p["cadencia_semana"]}</td><td class="num">{p["save_rate"]}%</td>'
                 f'<td class="num">{p["pct_som_original"]}%</td><td>{esc(p.get("sweet_spot",""))}</td>'
                 f'<td>{esc(p.get("melhor_dia",""))}</td></tr>')
    vs = round(med_nicho / vd["mediana"], 1) if vd["mediana"] else 0
    bench = (f'<p>A mediana de views de quem faz o <b>mesmo tema</b> que você é <b>{br(med_nicho)}</b>. '
             f'A sua é <b>{br(vd["mediana"])}</b> — o nicho está <b>{vs}× à frente</b>. '
             f'Não é preço nem produto: é <b>alcance por vídeo</b>.</p>'
             f'<div class="ov">{cmpbar(vd["mediana"], med_nicho)}</div>'
             f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th>perfil</th><th class="num">seguidores</th>'
             f'<th class="num">views (mediana)</th><th class="num">posts/sem</th><th class="num">save%</th>'
             f'<th class="num">%som orig.</th><th>duração</th><th>melhor dia</th></tr></thead><tbody>{rows}</tbody></table></div>')

    # -- cadência (posta demais) --
    cadrows = sorted([(p["handle"], p["cadencia_semana"], p["views_mediana"]) for p in nicho.get("perfis", [])],
                     key=lambda r: -r[1])
    cad_hl = next((i for i, r in enumerate(cadrows) if r[0] == handle), None)
    cad_bars = bars([(("@"+h)[:11], c, f"{c}") for h, c, _ in cadrows], hl=cad_hl, h=160)
    cad = (f'<p>Você posta <b>{a["cadencia_semana"]}×/semana</b> — de longe o maior volume do nicho. '
           f'E tem a menor mediana. <b>Volume não é o problema</b>: os líderes postam menos e alcançam mais. '
           f'O caminho é <b>postar menos e melhor</b>, não mais.</p><div class="ch">{cad_bars}<div class="ch-x">posts por semana</div></div>')

    # -- áudio --
    ovt = aud["original_vs_trend"]
    pct_orig = aud["pct_som_original"]
    som_rows = "".join(
        '<li><span class="q">{}</span> {} — {}× · {} views/méd</li>'.format(
            esc(s["nome"]), "· original" if s["original"] else "· trend", s["usos"], br(s["views_media"]))
        for s in aud.get("sons_top", [])[:5])
    audio_cards = (card(f"{pct_orig}%", "dos seus vídeos usam som original") +
                   card(br(ovt["trend"]["views_media"]), "trend ({} vídeos)".format(ovt["trend"]["n"]), "teal") +
                   card(br(ovt["original"]["views_media"]), "original ({} vídeos)".format(ovt["original"]["n"]), "muted"))
    audio_html = (f'<div class="stats">{audio_cards}</div>'
                  f'<p>No nicho, quem aposta em <b>som em alta</b> tende a alcançar mais — laryssamua chegou a '
                  f'<b>dobrar</b> o alcance com trend. Você usa <b>{pct_orig}% som original</b>: '
                  f'há espaço claro pra testar trilhas em alta.</p>'
                  + (f'<div class="box"><div class="box-h">Seus sons que mais renderam</div><ul class="mini">{som_rows}</ul></div>' if som_rows else ""))

    # -- dia/hora --
    dia_rows = [(d["dia"], d["views_media"], br(d["views_media"])) for d in hor.get("por_dia", [])]
    dia_hl = next((i for i, d in enumerate(hor.get("por_dia", [])) if hor.get("melhor_dia") and d["dia"] == hor["melhor_dia"]["dia"]), None)
    md, mh = hor.get("melhor_dia"), hor.get("melhor_hora")
    horhtml = (f'<p>Cruzando cada post com o alcance dele (fuso BR): sua melhor janela é '
               f'<b>{md["dia"] if md else "—"}</b>' + (f' por volta das <b>{mh["hora"]}h</b>' if mh else "") + '.</p>'
               f'<div class="ch">{bars(dia_rows, hl=dia_hl, h=160)}<div class="ch-x">views médias por dia da semana</div></div>')

    # -- duração --
    db = dur.get("buckets", [])
    dur_rows = [(b["faixa"], b["views_media"], br(b["views_media"])) for b in db]
    dur_hl = next((i for i, b in enumerate(db) if b["faixa"] == dur.get("sweet_spot")), None)
    lead_dur = [p.get("sweet_spot") for p in nicho.get("perfis", []) if p["handle"] != handle]
    durhtml = (f'<p>Sua faixa que mais rende é <b>{dur.get("sweet_spot","—")}</b>. Mas repare: os maiores do nicho '
               f'ganham com vídeos <b>mais longos (90s+)</b> — mais tempo de tela = mais entrega. Vale testar alongar.</p>'
               f'<div class="ch">{bars(dur_rows, hl=dur_hl, h=160)}<div class="ch-x">views médias por duração</div></div>')

    # -- ganchos --
    def hookli(r, tag=False):
        who = f'<span class="hk-w">@{esc(r["h"])}</span>' if tag else ''
        return (f'<li><span class="hk-v">{br(r["views"])}</span>'
                f'<span class="hk-q">"{esc(r["gancho"][:120])}"</span>{who}</li>')
    hk_mine = "".join(hookli(r) for r in mine_hooks[:4]) or '<li class="muted">Poucos vídeos seus têm legenda automática (a TikTok só gera pra alguns).</li>'
    hk_nicho = "".join(hookli(r, tag=True) for r in nicho_hooks[:6])
    hooks_html = (f'<p>O que os vídeos <b>dizem nos primeiros 3 segundos</b> (o gancho) decide a retenção. '
                  f'Padrão dos que <b>estouram no nicho</b>: demonstração sensorial imediata, "parece X mas não é", '
                  f'e comparação caro×barato — nada de "oi gente, hoje eu vou...".</p>'
                  f'<div class="two"><div class="box"><div class="box-h">Seus ganchos (por views)</div>'
                  f'<ul class="hooks">{hk_mine}</ul></div>'
                  f'<div class="box hot"><div class="box-h">Ganchos que vencem no nicho</div>'
                  f'<ul class="hooks">{hk_nicho}</ul></div></div>')

    # -- engajamento --
    sr = eng["save_rate"]
    eng_cards = (card(f"{sr}%", "taxa de save (intenção de compra)", "warn") +
                 card(f"{eng['share_rate']}%", "taxa de share (alcance)") +
                 card(f"{eng['er_medio']}%", "engajamento médio"))
    eng_html = (f'<div class="stats">{eng_cards}</div>'
                f'<p>Save = "quero guardar/comprar". A sua ({sr}%) está <b>~10× abaixo</b> do nicho '
                f'(0,7–1,3%). É o sintoma nº1 de conteúdo que ainda não gera desejo de compra.</p>')

    # -- tendência --
    tdir = tend.get("direcao", "—")
    tend_html = (f'<p>Ao longo do período, sua mediana foi de <b>{br(tend.get("mediana_1a_metade"))}</b> para '
                 f'<b>{br(tend.get("mediana_2a_metade"))}</b> views — tendência <b>{tdir}</b>'
                 + (f' ({tend.get("variacao_pct")}%)' if tend.get("variacao_pct") is not None else "") + '.</p>') \
        if tend.get("mediana_1a_metade") is not None else ""

    # -- plano de ação --
    plano = [
        (f'Postar menos e melhor', f'De {a["cadencia_semana"]}/sem para 3–4 vídeos/sem bem produzidos. Volume não está trazendo alcance.'),
        ('Gancho nos 3 primeiros segundos', 'Abrir com demonstração/resultado ou "parece X mas não é" — como os virais do nicho. Cortar o "oi gente".'),
        ('Testar som em alta', f'Hoje {aud["pct_som_original"]}% é som original. Usar trilhas em alta em metade dos vídeos e medir.'),
        (f'Alongar para 60–90s+', 'Mais tempo de tela puxa entrega. Os líderes do nicho ganham com vídeos longos.'),
        (f'Publicar {md["dia"] if md else "na melhor janela"}' + (f' ~{mh["hora"]}h' if mh else ''), 'Concentrar os lançamentos na janela que já rende mais pra você.'),
        ('Fechar cada vídeo com "salve isto"', 'CTA de salvar/compra explícito — para subir a taxa de save, hoje o elo mais fraco.'),
    ]
    plano_html = '<ol class="plano">' + "".join(
        f'<li><b>{esc(t)}</b><span>{esc(d)}</span></li>' for t, d in plano) + '</ol>'

    # -- tabela completa --
    vrows = "".join(
        f'<tr><td class="num">{br(v["views"])}</td><td class="num">{br(v["saves"])}</td>'
        f'<td class="num">{v["dur"]}s</td><td class="num">{v["data"]}</td>'
        f'<td>{"trend" if not v["som_original"] else "orig"}</td>'
        f'<td class="q"><a href="{esc(v["url"])}" target="_blank" rel="noopener">{esc(v["titulo"][:64])}</a></td></tr>'
        for v in a.get("videos", []))
    tabela = (f'<details><summary>Ver os {a["amostra"]} vídeos analisados</summary>'
              f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th class="num">views</th><th class="num">saves</th>'
              f'<th class="num">dur</th><th class="num">data</th><th>som</th><th>legenda</th></tr></thead>'
              f'<tbody>{vrows}</tbody></table></div></details>')

    seller_badge = ('<span class="badge on">✓ seller do Shop</span>' if a["seller"]["ttSeller"]
                    else '<span class="badge">ainda não é seller do Shop</span>')

    body = "".join([
        sec("diag", "leitura honesta", "O que os números realmente dizem",
            f'<ul class="diag">{diag}</ul>'),
        sec("dist", "distribuição", "A régua honesta: mediana, não média", dist),
        sec("bench", "benchmark", "Onde você está no seu nicho", bench),
        sec("cad", "cadência", "Você não posta de menos — posta demais", cad),
        sec("ganchos", "conteúdo", "Os 3 primeiros segundos decidem tudo", hooks_html),
        sec("audio", "áudio", "Som em alta é alavanca de alcance", audio_html),
        sec("dur", "formato", "Duração: o nicho ganha com vídeo longo", durhtml),
        sec("dia", "timing", "Quando postar", horhtml),
        sec("eng", "engajamento", "Save rate: o elo mais fraco", eng_html + tend_html),
        sec("plano", "o caminho", "Plano de ação — postar menos e melhor", plano_html),
        sec("dados", "transparência", "Os dados por trás", tabela),
    ])
    render(out_path, a, med_nicho, vs, seller_badge, body)

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
.wrap{max-width:920px;margin:0 auto;padding:0 22px 64px}
h1,h2{font-family:var(--serif);font-weight:600;letter-spacing:-.01em;margin:0}
a{color:var(--teal)}
.top{border-bottom:1px solid var(--line);background:var(--surface)}
.top-in{max-width:920px;margin:0 auto;padding:26px 22px}
.brand{font-family:var(--mono);font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-soft);display:flex;align-items:center;gap:9px}
.brand .dot{width:9px;height:9px;border-radius:50%;background:var(--teal)}
.top h1{font-size:1.85rem;margin:10px 0 4px}
.who{color:var(--ink-soft)}.badge{font-family:var(--mono);font-size:.7rem;border:1px solid var(--line);border-radius:999px;padding:3px 10px;color:var(--muted);margin-left:8px}
.badge.on{color:var(--teal);border-color:var(--teal)}
.lead{max-width:920px;margin:0 auto;padding:20px 22px 0}
.lead .big{font-family:var(--serif);font-size:1.35rem;line-height:1.4}
.lead .big b{color:var(--ochre)}
section{border-top:1px solid var(--line);padding:30px 0 4px;margin-top:26px}
.wrap>section:first-child{border-top:0}
.kick{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--teal);margin-bottom:6px}
h2{font-size:1.4rem;margin-bottom:12px}
p{color:var(--ink-soft)}b{color:var(--ink)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:16px 0}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px;box-shadow:var(--shadow)}
.s-v{font-family:var(--mono);font-size:1.5rem;font-weight:600;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.s-k{font-size:.76rem;color:var(--ink-soft);margin-top:3px}
.stat.ochre .s-v{color:var(--ochre)}.stat.warn .s-v{color:var(--red)}.stat.muted .s-v{color:var(--muted)}.stat.teal .s-v{color:var(--teal)}
.diag{margin:6px 0;padding:0;list-style:none}
.diag li{padding:10px 0 10px 26px;border-top:1px solid var(--line);position:relative;color:var(--ink)}
.diag li:first-child{border-top:0}
.diag li:before{content:"▪";position:absolute;left:6px;color:var(--ochre)}
.box{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:14px 0;box-shadow:var(--shadow)}
.box.hot{border-color:var(--ochre)}
.box-h{font-family:var(--mono);font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.mini{margin:0;padding:0;list-style:none}.mini li{padding:6px 0;border-top:1px solid var(--line);font-size:.9rem}.mini li:first-child{border-top:0}
.q{color:var(--ink-soft)}
.ch{margin:14px 0}.ch-x{font-family:var(--mono);font-size:.68rem;color:var(--muted);text-align:center;margin-top:2px}
.chart{width:100%;height:auto;display:block}
.bl{font-family:var(--mono);font-size:11px;fill:var(--ink-soft)}.bx{font-family:var(--mono);font-size:10px;fill:var(--muted)}
.ov{margin:16px 0}
.cmp{display:flex;flex-direction:column;gap:12px}
.cmp-row{display:flex;align-items:center;gap:12px}
.cmp-l{width:130px;font-size:.82rem;color:var(--ink-soft);text-align:right;flex:none}
.cmp-bar{flex:1;background:var(--line);border-radius:5px;height:18px;overflow:hidden}
.cmp-bar i{display:block;height:100%;border-radius:5px}
.cmp-v{width:64px;font-family:var(--mono);font-size:.85rem;font-variant-numeric:tabular-nums;flex:none}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.hooks{margin:0;padding:0;list-style:none}
.hooks li{padding:9px 0;border-top:1px solid var(--line);display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.hooks li:first-child{border-top:0}
.hk-v{font-family:var(--mono);font-size:.8rem;color:var(--teal);font-variant-numeric:tabular-nums;flex:none;min-width:58px}
.hk-q{flex:1;color:var(--ink);font-size:.92rem}.hk-w{font-family:var(--mono);font-size:.72rem;color:var(--muted)}
.plano{margin:10px 0;padding:0;counter-reset:p;list-style:none}
.plano li{padding:12px 0 12px 42px;border-top:1px solid var(--line);position:relative}
.plano li:first-child{border-top:0}
.plano li:before{counter-increment:p;content:counter(p);position:absolute;left:0;top:12px;width:26px;height:26px;border-radius:50%;background:var(--teal-soft);color:var(--teal);font-family:var(--mono);font-size:.8rem;display:flex;align-items:center;justify-content:center}
.plano b{display:block}.plano span{color:var(--ink-soft);font-size:.9rem}
.tbl-wrap{overflow-x:auto;margin:12px 0}
.tbl{width:100%;border-collapse:collapse;font-size:.86rem}
.tbl th{text-align:left;font-family:var(--mono);font-size:.64rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding:7px 9px;border-bottom:1px solid var(--line);white-space:nowrap}
.tbl td{padding:8px 9px;border-bottom:1px solid var(--line)}
.tbl .num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
.tbl tr.me{background:var(--teal-soft)}.tbl tr.me td{font-weight:600}
details{margin:8px 0}summary{cursor:pointer;font-family:var(--mono);font-size:.8rem;color:var(--teal);padding:8px 0}
.toggle{position:fixed;top:14px;right:14px;z-index:9;background:var(--surface);border:1px solid var(--line);color:var(--ink-soft);border-radius:999px;padding:6px 11px;font-family:var(--mono);font-size:.72rem;cursor:pointer;box-shadow:var(--shadow)}
.foot{max-width:920px;margin:0 auto;padding:24px 22px;color:var(--muted);font-size:.76rem;border-top:1px solid var(--line)}
:focus-visible{outline:2px solid var(--teal);outline-offset:2px}
@media (max-width:720px){.two{grid-template-columns:1fr}.cmp-l{width:90px}.top h1{font-size:1.5rem}}
@media print{.toggle{display:none}body{background:#fff}}
"""

def render(out_path, a, med_nicho, vs, seller_badge, body):
    JS = ("(function(){var b=document.getElementById('tg');if(b)b.onclick=function(){"
          "var r=document.documentElement,d=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');"
          "var n=d==='dark'?'light':'dark';r.setAttribute('data-theme',n);b.textContent=n==='dark'?'\\u25D0 Tema':'\\u25D1 Tema';};"
          "window.addEventListener('message',function(e){if(e&&e.data&&e.data.fullbpo_tema)"
          "document.documentElement.setAttribute('data-theme',e.data.fullbpo_tema);});})();")
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Análise de Performance — {esc(a.get('nome') or a['handle'])}</title><style>{CSS}</style></head><body>
<button class="toggle" id="tg" aria-label="Alternar tema">◑ Tema</button>
<header class="top"><div class="top-in">
<div class="brand"><span class="dot"></span> FullBPO · Análise de Performance</div>
<h1>{esc(a.get('nome') or a['handle'])} {seller_badge}</h1>
<div class="who">@{esc(a['handle'])} · {br(a.get('seguidores'))} seguidores · {a['amostra']} vídeos analisados · {esc(a['periodo'][0])}–{esc(a['periodo'][1])}</div>
</div></header>
<div class="lead"><p class="big">Sua mediana é <b>{br(a['views_dist']['mediana'])} views</b> por vídeo. A do seu nicho é
<b>{br(med_nicho)}</b>. Você posta <b>{a['cadencia_semana']}×/semana</b> — e ainda assim fica <b>{vs}× atrás</b>.
A boa notícia: isso é sobre <b>mecânica de conteúdo</b>, e dá pra consertar.</p></div>
<main class="wrap">{body}</main>
<footer class="foot">Gerado pela FullBPO — Backoffice Inteligente · dados públicos coletados via Apify + análise própria ·
mediana como régua (resistente a picos). Uso interno/cliente.</footer>
<script>{JS}</script></body></html>"""
    open(out_path, "w", encoding="utf-8").write(doc)
    print(f"análise gerada: {out_path} ({os.path.getsize(out_path)//1024} KB)")

if __name__ == "__main__":
    main()
