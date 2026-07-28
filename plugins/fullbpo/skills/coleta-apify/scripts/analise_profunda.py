#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# analise_profunda.py — extrai a ANÁLISE PROFUNDA de um perfil a partir do
# dataset CRU do actor (clockworks/tiktok-scraper). O apify.py/mapear_perfil
# colapsa tudo em ~8 médias; aqui a gente NÃO joga o cru fora e responde:
#   - Áudio em alta (som original vs trend, quais sons rendem mais alcance)
#   - Melhor DIA e HORA de postar (fuso BR, UTC-3)
#   - Duração × desempenho (faixa ideal + correlação)
#   - Distribuição HONESTA (mediana, outliers, consistência) — média mente
#   - Taxas de save (intenção de compra) e share (alcance) por vídeo
#   - Colabs (@menções), tendência no tempo, hashtags que performam
#   - É seller do Shop? (authorMeta) + padrões de legenda/CTA
#   - Correlações (o que realmente move views)
#   - Tabela dos vídeos TODOS (não só top-5) + diagnóstico auto
#
# Uso:
#   python3 analise_profunda.py <raw.json> [analise.json]     # 1 perfil
#   python3 analise_profunda.py --nicho <a.raw.json> <b.raw.json> ... -o nicho.json
#   python3 analise_profunda.py autotest
#
# Só stdlib. TZ BR fixa em UTC-3 (sem depender de tzdata).
# ---------------------------------------------------------------------------
import sys, os, json, re, math, statistics as st
from datetime import datetime, timezone, timedelta

BR_TZ = timezone(timedelta(hours=-3))
DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# ---------- helpers numéricos (sem numpy) ----------------------------------
def g(v, k):
    x = v.get(k)
    return x if isinstance(x, (int, float)) else 0

def _pearson(xs, ys):
    n = len(xs)
    if n < 3: return None
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0: return None
    return round(num / (dx * dy), 2)

def _iso(s):
    try: return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception: return None

def _fdate(dt): return dt.astimezone(BR_TZ).strftime("%d/%m/%Y") if dt else ""

def _safe_media(xs): return int(st.mean(xs)) if xs else 0
def _safe_med(xs):   return int(st.median(xs)) if xs else 0

# ---------- núcleo --------------------------------------------------------
def analisar(items, benchmark_mediana=None):
    """Recebe a lista CRUA de vídeos do actor e devolve o dossiê profundo."""
    vids = [v for v in items if v.get("playCount") is not None]
    if not vids:
        raise SystemExit("ERRO: nenhum vídeo com métricas no cru.")
    am = (vids[0].get("authorMeta") or {})

    views  = [g(v, "playCount")   for v in vids]
    likes  = [g(v, "diggCount")   for v in vids]
    coms   = [g(v, "commentCount") for v in vids]
    shares = [g(v, "shareCount")  for v in vids]
    saves  = [g(v, "collectCount") for v in vids]
    durs   = [(v.get("videoMeta") or {}).get("duration") or 0 for v in vids]
    dts    = [_iso(v.get("createTimeISO")) for v in vids]

    med_views = _safe_med(views)
    mean_views = _safe_media(views)
    std_views = round(st.pstdev(views), 1) if len(views) > 1 else 0.0

    # ---- distribuição honesta (média mente quando há pico isolado) --------
    def _q(p):
        s = sorted(views); i = min(len(s) - 1, int(round(p * (len(s) - 1))))
        return s[i]
    outliers = []
    for v in sorted(vids, key=lambda v: -g(v, "playCount")):
        vw = g(v, "playCount")
        if med_views and vw >= 3 * med_views:
            outliers.append({"views": vw, "mult_mediana": round(vw / med_views, 1),
                             "titulo": (v.get("text") or "")[:70],
                             "url": v.get("webVideoUrl") or v.get("url"),
                             "data": _fdate(_iso(v.get("createTimeISO")))})
    total_views = sum(views) or 1
    views_dist = {
        "media": mean_views, "mediana": med_views,
        "p25": _q(0.25), "p75": _q(0.75), "p90": _q(0.90),
        "min": min(views), "max": max(views),
        "desvio": std_views,
        "cv": round(std_views / mean_views, 2) if mean_views else 0,   # consistência
        "media_sobre_mediana": round(mean_views / med_views, 1) if med_views else 0,
        "n_outliers": len(outliers), "outliers": outliers[:5],
        "concentracao_top_pct": round(max(views) / total_views * 100, 1),
        "pct_abaixo_1k": round(sum(1 for x in views if x < 1000) / len(views) * 100),
    }
    if benchmark_mediana:
        views_dist["mediana_nicho"] = benchmark_mediana
        views_dist["vs_nicho"] = round(med_views / benchmark_mediana, 2) if benchmark_mediana else None

    # ---- engajamento por taxa (não só um proxy) --------------------------
    def _rate(nums): return round(st.mean([n / (v or 1) for n, v in zip(nums, views)]) * 100, 2)
    eng = {
        "like_rate": _rate(likes), "comment_rate": _rate(coms),
        "share_rate": _rate(shares), "save_rate": _rate(saves),
        "er_medio": round(st.mean([(likes[i]+coms[i]+shares[i]+saves[i])/(views[i] or 1)
                                   for i in range(len(vids))]) * 100, 2),
    }
    best = lambda key: max(vids, key=lambda v: g(v, key) / (g(v, "playCount") or 1))
    bs = best("collectCount")
    eng["melhor_save"] = {"titulo": (bs.get("text") or "")[:60], "save_rate": round(g(bs,"collectCount")/(g(bs,"playCount") or 1)*100,2),
                          "url": bs.get("webVideoUrl") or bs.get("url")}

    # ---- áudio: som original vs trend, quais sons rendem ------------------
    sons = {}
    for v in vids:
        m = v.get("musicMeta") or {}
        key = m.get("musicId") or m.get("musicName") or "?"
        d = sons.setdefault(key, {"nome": m.get("musicName") or "som", "autor": m.get("musicAuthor") or "",
                                  "original": bool(m.get("musicOriginal")), "usos": 0, "_views": []})
        d["usos"] += 1; d["_views"].append(g(v, "playCount"))
    for d in sons.values():
        d["views_media"] = _safe_media(d["_views"]); d.pop("_views")
    orig = [g(v, "playCount") for v in vids if (v.get("musicMeta") or {}).get("musicOriginal")]
    trend = [g(v, "playCount") for v in vids if not (v.get("musicMeta") or {}).get("musicOriginal")]
    audio = {
        "total_sons": len(sons),
        "pct_som_original": round(len(orig) / len(vids) * 100),
        "sons_top": sorted(sons.values(), key=lambda d: -d["views_media"])[:8],
        "original_vs_trend": {
            "original": {"n": len(orig), "views_media": _safe_media(orig)},
            "trend": {"n": len(trend), "views_media": _safe_media(trend)},
        },
    }

    # ---- melhor dia/hora (fuso BR) ---------------------------------------
    por_dia = {i: [] for i in range(7)}
    por_hora = {}
    for v, dt in zip(vids, dts):
        if not dt: continue
        b = dt.astimezone(BR_TZ)
        por_dia[b.weekday()].append(g(v, "playCount"))
        por_hora.setdefault(b.hour, []).append(g(v, "playCount"))
    dia_stats = [{"dia": DIAS[i], "n": len(vs), "views_media": _safe_media(vs)} for i, vs in por_dia.items() if vs]
    hora_stats = [{"hora": h, "n": len(vs), "views_media": _safe_media(vs)} for h, vs in sorted(por_hora.items())]
    horario = {
        "por_dia": dia_stats, "por_hora": hora_stats,
        # exige amostra mínima (n>=2) p/ não deixar 1 pico isolado sequestrar a "melhor" janela
        "melhor_dia": max([d for d in dia_stats if d["n"] >= 2] or dia_stats, key=lambda d: d["views_media"]) if dia_stats else None,
        "melhor_hora": max([d for d in hora_stats if d["n"] >= 2] or hora_stats, key=lambda d: d["views_media"]) if hora_stats else None,
    }

    # ---- duração × views -------------------------------------------------
    faixas = [("0-15s", 0, 15), ("16-30s", 16, 30), ("31-60s", 31, 60), ("61-90s", 61, 90), ("90s+", 91, 10**6)]
    dur_buckets = []
    for nome, lo, hi in faixas:
        vs = [g(v, "playCount") for v, d in zip(vids, durs) if lo <= d <= hi]
        if vs: dur_buckets.append({"faixa": nome, "n": len(vs), "views_media": _safe_media(vs)})
    duracao = {
        "media": round(st.mean(durs)) if durs else 0, "mediana": _safe_med(durs),
        "buckets": dur_buckets,
        "corr_dur_views": _pearson(durs, views),
        "sweet_spot": max(dur_buckets, key=lambda d: d["views_media"])["faixa"] if dur_buckets else None,
    }

    # ---- tendência no tempo ---------------------------------------------
    seq = sorted([(dt, g(v, "playCount")) for v, dt in zip(vids, dts) if dt], key=lambda x: x[0])
    tendencia = {"direcao": "sem dados"}
    if len(seq) >= 4:
        meio = len(seq) // 2
        m1 = _safe_med([x[1] for x in seq[:meio]])
        m2 = _safe_med([x[1] for x in seq[meio:]])
        t0 = seq[0][0].timestamp()
        xs = [(dt.timestamp() - t0) / 86400 for dt, _ in seq]
        r = _pearson(xs, [vw for _, vw in seq])
        tendencia = {
            "mediana_1a_metade": m1, "mediana_2a_metade": m2,
            "variacao_pct": round((m2 - m1) / m1 * 100) if m1 else None,
            "corr_tempo_views": r,
            "direcao": "subindo" if m2 > m1 * 1.15 else "caindo" if m2 < m1 * 0.85 else "estável",
        }

    # ---- hashtags que performam -----------------------------------------
    tag_views = {}
    for v in vids:
        tags = {("#" + (h.get("name") if isinstance(h, dict) else str(h))).lower()
                for h in (v.get("hashtags") or [])}
        tags |= {t.lower() for t in re.findall(r"#\w+", v.get("text") or "")}
        for t in tags:
            tag_views.setdefault(t, []).append(g(v, "playCount"))
    hashtags = {
        "top_uso": sorted([(t, len(vs)) for t, vs in tag_views.items()], key=lambda x: -x[1])[:12],
        "melhores": sorted([{"tag": t, "usos": len(vs), "views_media": _safe_media(vs)}
                            for t, vs in tag_views.items() if len(vs) >= 2],
                           key=lambda d: -d["views_media"])[:8],
    }

    # ---- colabs (@menções) ----------------------------------------------
    ments = {}
    n_colab = 0
    for v in vids:
        ms = set()
        for m in (v.get("mentions") or []):
            ms.add((m.get("name") if isinstance(m, dict) else str(m)).lstrip("@"))
        ms |= {x.lstrip("@") for x in re.findall(r"@[\w.]+", v.get("text") or "")}
        ms.discard(am.get("name") or "")
        ms.discard("")
        if ms: n_colab += 1
        for m in ms: ments[m] = ments.get(m, 0) + 1
    colabs = {
        "total_creators": len(ments), "pct_videos_com_colab": round(n_colab / len(vids) * 100),
        "top": sorted([{"handle": k, "vezes": n} for k, n in ments.items()], key=lambda d: -d["vezes"])[:8],
    }

    # ---- padrões de legenda / CTA ---------------------------------------
    caps = [v.get("text") or "" for v in vids]
    cta_re = re.compile(r"link|bio|clique|clica|garant|compr|cupom|desconto|arrast|shop", re.I)
    conteudo_texto = {
        "legenda_len_media": round(st.mean([len(c) for c in caps])),
        "pct_com_cta": round(sum(1 for c in caps if cta_re.search(c)) / len(caps) * 100),
        "pct_com_pergunta": round(sum(1 for c in caps if "?" in c) / len(caps) * 100),
        "hashtags_por_video": round(st.mean([len(re.findall(r"#\w+", c)) for c in caps]), 1),
    }

    # ---- correlações resumidas ------------------------------------------
    len_caps = [len(c) for c in caps]
    trend_flag = [0 if (v.get("musicMeta") or {}).get("musicOriginal") else 1 for v in vids]
    correlacoes = {
        "duracao_x_views": duracao["corr_dur_views"],
        "legenda_len_x_views": _pearson(len_caps, views),
        "som_trend_x_views_delta": (round(audio["original_vs_trend"]["trend"]["views_media"]
                                          - audio["original_vs_trend"]["original"]["views_media"])
                                    if orig and trend else None),
    }

    # ---- tabela completa (todos os vídeos) -------------------------------
    tabela = sorted([{
        "views": g(v, "playCount"), "likes": g(v, "diggCount"), "coments": g(v, "commentCount"),
        "shares": g(v, "shareCount"), "saves": g(v, "collectCount"),
        "dur": (v.get("videoMeta") or {}).get("duration") or 0,
        "data": _fdate(_iso(v.get("createTimeISO"))),
        "som": (v.get("musicMeta") or {}).get("musicName") or "",
        "som_original": bool((v.get("musicMeta") or {}).get("musicOriginal")),
        "save_rate": round(g(v, "collectCount") / (g(v, "playCount") or 1) * 100, 2),
        "titulo": (v.get("text") or "")[:80], "url": v.get("webVideoUrl") or v.get("url"),
    } for v in vids], key=lambda r: -r["views"])

    ci = (am.get("commerceUserInfo") or {})
    seller = {
        "ttSeller": bool(am.get("ttSeller")),
        "commerce": bool(ci.get("commerceUser") or am.get("ttSeller")),
        "categoria": ci.get("category") or "",
        "bioLink": am.get("bioLink") or "",
    }

    dt_ok = [d for d in dts if d]
    dmin, dmax = (min(dt_ok), max(dt_ok)) if dt_ok else (None, None)
    dias = max(1, (dmax - dmin).days) if dt_ok else 1

    out = {
        "handle": am.get("name") or "", "nome": am.get("nickName") or "",
        "seguidores": am.get("fans"), "curtidas_totais": am.get("heart"),
        "verificado": bool(am.get("verified")), "bio": am.get("signature") or "",
        "seller": seller,
        "amostra": len(vids), "periodo": [_fdate(dmin), _fdate(dmax)], "dias": dias,
        "cadencia_semana": round(len(vids) / dias * 7, 1),
        "views_dist": views_dist, "engajamento": eng, "audio": audio,
        "horario": horario, "duracao": duracao, "tendencia": tendencia,
        "hashtags": hashtags, "colabs": colabs, "conteudo_texto": conteudo_texto,
        "correlacoes": correlacoes, "videos": tabela,
    }
    out["diagnostico"] = _diagnostico(out)
    return out

# ---------- diagnóstico automático (bullets prontos) -----------------------
def _diagnostico(a):
    d = []
    vd = a["views_dist"]
    if vd["media_sobre_mediana"] >= 2:
        d.append(f"A média de views ({vd['media']:,}) é {vd['media_sobre_mediana']}× a mediana "
                 f"({vd['mediana']:,}) — está inflada por {vd['n_outliers']} pico(s). A mediana é a régua honesta."
                 .replace(",", "."))
    if vd["pct_abaixo_1k"] >= 50:
        d.append(f"{vd['pct_abaixo_1k']}% dos vídeos ficam abaixo de 1.000 views — alcance travado na base.")
    ovt = a["audio"]["original_vs_trend"]
    if ovt["trend"]["n"] and ovt["original"]["n"]:
        if ovt["trend"]["views_media"] > ovt["original"]["views_media"] * 1.3:
            d.append(f"Som em ALTA rende {round(ovt['trend']['views_media']/max(1,ovt['original']['views_media']),1)}× "
                     f"mais que som original ({ovt['trend']['views_media']:,} vs {ovt['original']['views_media']:,} views). "
                     f"Hoje {a['audio']['pct_som_original']}% dos vídeos usam som original.".replace(",", "."))
    if a["horario"].get("melhor_dia") and a["horario"].get("melhor_hora"):
        d.append(f"Melhor janela: {a['horario']['melhor_dia']['dia']} por volta das "
                 f"{a['horario']['melhor_hora']['hora']}h (horário BR).")
    if a["duracao"].get("sweet_spot"):
        d.append(f"Faixa de duração que mais rende: {a['duracao']['sweet_spot']}.")
    tr = a["tendencia"]
    if tr.get("direcao") in ("subindo", "caindo"):
        d.append(f"Tendência {tr['direcao']}: mediana passou de {tr['mediana_1a_metade']:,} para "
                 f"{tr['mediana_2a_metade']:,} views entre a 1ª e a 2ª metade do período.".replace(",", "."))
    if a["engajamento"]["save_rate"] < 0.5:
        d.append(f"Taxa de save baixa ({a['engajamento']['save_rate']}%) — pouca intenção de salvar/voltar; "
                 f"conteúdo ainda não gera 'quero comprar/guardar'.")
    if a["seller"]["ttSeller"]:
        d.append("Perfil já marcado como SELLER do TikTok Shop.")
    return d

# ---------- benchmark do nicho --------------------------------------------
def nicho(analises):
    """Consolida vários perfis já analisados num quadro comparativo."""
    med_nicho = _safe_med([a["views_dist"]["mediana"] for a in analises if a["views_dist"]["mediana"]])
    linhas = []
    for a in analises:
        linhas.append({
            "handle": a["handle"], "nome": a["nome"], "seguidores": a["seguidores"],
            "views_mediana": a["views_dist"]["mediana"], "views_media": a["views_dist"]["media"],
            "cadencia_semana": a["cadencia_semana"], "er_medio": a["engajamento"]["er_medio"],
            "save_rate": a["engajamento"]["save_rate"], "share_rate": a["engajamento"]["share_rate"],
            "pct_som_original": a["audio"]["pct_som_original"],
            "melhor_dia": (a["horario"].get("melhor_dia") or {}).get("dia", ""),
            "sweet_spot": a["duracao"].get("sweet_spot", ""),
            "seller": a["seller"]["ttSeller"],
        })
    linhas.sort(key=lambda r: -(r["views_mediana"] or 0))
    return {"mediana_nicho": med_nicho, "perfis": linhas}

# ---------- CLI ------------------------------------------------------------
AMOSTRA = [
    {"playCount": 11300, "diggCount": 31, "commentCount": 2, "shareCount": 14, "collectCount": 5,
     "text": "kit de pincéis que mudou tudo #maquiagem #pinceis @loja", "createTimeISO": "2026-07-03T22:00:17.000Z",
     "hashtags": [{"name": "maquiagem"}, {"name": "pinceis"}], "mentions": [{"name": "loja"}],
     "musicMeta": {"musicId": "t1", "musicName": "trend viral", "musicOriginal": False, "musicAuthor": "DJ"},
     "videoMeta": {"duration": 22}, "webVideoUrl": "u1",
     "authorMeta": {"name": "pri.andrade50", "nickName": "Pri Andrade", "fans": 2006, "heart": 5000, "verified": False, "ttSeller": False, "signature": "afiliada"}},
    {"playCount": 90, "diggCount": 2, "commentCount": 0, "shareCount": 0, "collectCount": 0,
     "text": "bastidor do dia a dia", "createTimeISO": "2026-07-10T13:00:00.000Z",
     "hashtags": [{"name": "rotina"}], "musicMeta": {"musicId": "orig", "musicName": "som original", "musicOriginal": True},
     "videoMeta": {"duration": 55}, "webVideoUrl": "u2", "authorMeta": {"name": "pri.andrade50", "fans": 2006}},
    {"playCount": 60, "diggCount": 1, "commentCount": 0, "shareCount": 0, "collectCount": 0,
     "text": "mais um vídeo #maquiagem", "createTimeISO": "2026-07-20T20:00:00.000Z",
     "hashtags": [{"name": "maquiagem"}], "musicMeta": {"musicId": "orig", "musicName": "som original", "musicOriginal": True},
     "videoMeta": {"duration": 48}, "webVideoUrl": "u3", "authorMeta": {"name": "pri.andrade50", "fans": 2006}},
    {"playCount": 43, "diggCount": 0, "commentCount": 0, "shareCount": 0, "collectCount": 0,
     "text": "testando produto novo", "createTimeISO": "2026-07-24T21:00:00.000Z",
     "musicMeta": {"musicId": "t1", "musicName": "trend viral", "musicOriginal": False},
     "videoMeta": {"duration": 30}, "webVideoUrl": "u4", "authorMeta": {"name": "pri.andrade50", "fans": 2006}},
]

def main():
    a = sys.argv[1:]
    if a and a[0] == "autotest":
        r = analisar(AMOSTRA)
        assert r["views_dist"]["mediana"] == 75 and r["views_dist"]["media"] == 2873, ("dist", r["views_dist"])
        assert r["views_dist"]["media_sobre_mediana"] >= 2, "skew"
        assert r["views_dist"]["n_outliers"] == 1, "outlier (pico isolado)"
        assert r["audio"]["original_vs_trend"]["trend"]["views_media"] > r["audio"]["original_vs_trend"]["original"]["views_media"], "trend>orig"
        assert r["horario"]["melhor_dia"] and r["duracao"]["sweet_spot"], "dia/dur"
        assert r["colabs"]["total_creators"] == 1, "colab"
        assert any("média" in d.lower() for d in r["diagnostico"]), "diag"
        n = nicho([r, r])
        assert n["mediana_nicho"] == 75 and len(n["perfis"]) == 2, "nicho"
        print("AUTOTEST OK — análise profunda válida")
        print(json.dumps({k: r[k] for k in ("views_dist", "audio", "horario", "duracao", "diagnostico")},
                         ensure_ascii=False, indent=2)[:1200])
        return
    if a and a[0] == "--nicho":
        rest, out = a[1:], "nicho_analise.json"
        if "-o" in rest:
            i = rest.index("-o"); out = rest[i + 1]; rest = rest[:i] + rest[i + 2:]
        raws = [x for x in rest if not x.startswith("-")]
        analises = []
        for r in raws:
            try: analises.append(analisar(json.load(open(r))))
            except Exception as e: print(f">> aviso: {r} falhou: {e}", file=sys.stderr)
        res = {"nicho": nicho(analises), "perfis": analises}
        json.dump(res, open(out, "w"), ensure_ascii=False, indent=2)
        print(f"nicho salvo: {out} — {len(analises)} perfis | mediana do nicho {res['nicho']['mediana_nicho']:,}".replace(",", "."))
        return
    if not a:
        print(__doc__ or "uso: analise_profunda.py <raw.json> [analise.json]"); sys.exit(2)
    raw = a[0]; saida = a[1] if len(a) > 1 and not a[1].startswith("-") else "analise.json"
    res = analisar(json.load(open(raw)))
    json.dump(res, open(saida, "w"), ensure_ascii=False, indent=2)
    print(f"análise salva: {saida} — @{res['handle']} | mediana {res['views_dist']['mediana']:,} views | "
          f"{len(res['diagnostico'])} insights".replace(",", "."))

if __name__ == "__main__":
    main()
