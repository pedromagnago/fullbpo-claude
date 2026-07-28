#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# apify.py — adaptador Apify -> modelo normalizado da FullBPO.
# Roda um actor do Apify e mapeia a saída para os JSONs que os renderizadores
# consomem (perfil_analise.json / produtos.json).
#
# Uso:
#   APIFY_TOKEN=... python3 apify.py perfil <@handle|url> [saida.json] [--n 30]
#   APIFY_TOKEN=... python3 apify.py produtos "<palavra|url>" [saida.json] [--n 100] [--top 20]
#   APIFY_TOKEN=... python3 apify.py descobrir "<categoria1,categoria2,...>" [saida.json] \
#       [--n 20] [--lang pt] [--min-seg 20000] [--max-seg 2000000] [--excluir @handle]
#       (use termos de CATEGORIA p/ achar referências; --min-seg alto p/ estabelecidos)
#   python3 apify.py autotest        # testa os mapeadores em amostra (sem token/rede)
#
# Actors (sobrescreva por env se quiser outro):
#   APIFY_ACTOR_PERFIL   (padrão clockworks/tiktok-scraper)
#   APIFY_ACTOR_PRODUTOS (padrão trakk/tiktok-shop-search-scraper)
#   APIFY_PROXY_COUNTRY  país do proxy p/ produtos, ex.: BR (precisa de proxy
#                        residencial no plano Apify; sem isso, retorna US/global)
#   APIFY_MIN_VENDAS     venda mínima p/ manter um produto (padrão 1; 0 = tudo)
#   APIFY_LANG           idioma p/ filtrar creators na descoberta (padrão pt)
#
# Rede: usa só stdlib (urllib) e respeita HTTPS_PROXY + CA do ambiente.
# ---------------------------------------------------------------------------
import os, sys, json, re, statistics as st
from datetime import datetime, timezone

APIFY_BASE = "https://api.apify.com/v2"
ACTOR_PERFIL = os.environ.get("APIFY_ACTOR_PERFIL", "clockworks/tiktok-scraper")
ACTOR_PRODUTOS = os.environ.get("APIFY_ACTOR_PRODUTOS", "trakk/tiktok-shop-search-scraper")

def run_actor(actor, inp, token, timeout=600):
    """Roda um actor de forma síncrona e devolve os itens do dataset."""
    import urllib.request, urllib.error
    actor = actor.replace("/", "~")                       # a API usa ~ no lugar de /
    url = f"{APIFY_BASE}/acts/{actor}/run-sync-get-dataset-items?token={token}"
    req = urllib.request.Request(url, data=json.dumps(inp).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:500]
        raise SystemExit(f"ERRO Apify {e.code}: {body}")

# --------------------------- mapeadores -------------------------------------
def _iso_ts(s):
    try: return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except Exception: return None

def mapear_perfil(items):
    """clockworks/tiktok-scraper (itens de vídeo) -> perfil_analise.json (+ extras)."""
    vids = [v for v in items if v.get("playCount") is not None]
    if not vids:
        raise SystemExit("ERRO: nenhum vídeo com métricas na resposta do actor.")
    g = lambda v, k: v.get(k) or 0
    views  = [g(v, "playCount")    for v in vids]
    likes  = [g(v, "diggCount")    for v in vids]
    coms   = [g(v, "commentCount") for v in vids]
    shares = [g(v, "shareCount")   for v in vids]
    saves  = [g(v, "collectCount") for v in vids]
    durs   = [(v.get("videoMeta") or {}).get("duration") or 0 for v in vids]
    ts     = [t for t in (_iso_ts(v.get("createTimeISO")) for v in vids) if t]
    dmin, dmax = (min(ts), max(ts)) if ts else (0, 0)
    days = max(1, (dmax - dmin) / 86400) if ts else 1
    er = lambda v: (g(v,"diggCount")+g(v,"commentCount")+g(v,"shareCount")+g(v,"collectCount"))/(g(v,"playCount") or 1)
    tags = {}
    for v in vids:                                   # conta cada tag 1x por vídeo
        seen = set()
        for h in (v.get("hashtags") or []):
            raw = h.get("name") if isinstance(h, dict) else h
            if raw: seen.add(("#" + str(raw).lstrip("#")).lower())   # ignora nome vazio
        for m in re.findall(r"#\w+", v.get("text") or ""):
            seen.add(m.lower())
        for nm in seen:
            tags[nm] = tags.get(nm, 0) + 1
    top_tags = sorted(tags.items(), key=lambda x: -x[1])[:12]
    top = sorted(vids, key=lambda v: -g(v, "playCount"))[:5]
    fdate = lambda t: datetime.fromtimestamp(t, tz=timezone.utc).strftime("%d/%m/%Y")
    am = (vids[0].get("authorMeta") or {})
    return {
        "handle": am.get("name") or "",
        "nome": am.get("nickName") or "",
        "seguidores": am.get("fans"),
        "curtidas_totais": am.get("heart"),
        "verificado": am.get("verified"),
        "bio": am.get("signature") or "",
        "amostra": len(vids),
        "periodo": [fdate(dmin), fdate(dmax)] if ts else ["", ""],
        "dias": round(days),
        "cadencia_semana": round(len(vids) / days * 7, 1),
        "views": {"media": int(st.mean(views)), "mediana": int(st.median(views)),
                  "min": min(views), "max": max(views)},
        "likes_media": int(st.mean(likes)), "coment_media": int(st.mean(coms)),
        "shares_media": int(st.mean(shares)), "saves_media": int(st.mean(saves)),
        "engajamento_proxy": round(st.mean([er(v) for v in vids]) * 100, 1),
        "duracao_media": round(st.mean(durs)) if durs else 0,
        "top_hashtags": top_tags,
        "top_videos": [{"views": g(v,"playCount"), "likes": g(v,"diggCount"),
                        "data": fdate(_iso_ts(v.get("createTimeISO"))) if _iso_ts(v.get("createTimeISO")) else "",
                        "titulo": (v.get("text") or "")[:70],
                        "url": v.get("webVideoUrl") or v.get("url")} for v in top],
    }

def _first(d, *keys):
    for k in keys:
        if d.get(k) not in (None, ""): return d[k]
    return None

def mapear_produtos(items):
    """Actor de TikTok Shop -> lista normalizada de produtos (tolerante a nomes de campo)."""
    out = []
    for it in items:
        nome = _first(it, "title", "productName", "name", "product_title")
        if not nome: continue
        preco = _first(it, "currentPrice", "price", "salePrice", "priceValue", "minPrice")
        vendas = _first(it, "soldCount", "sales", "salesCount", "sold", "orderCount")
        receita = _first(it, "revenue", "gmv", "estimatedRevenue", "salesAmount")
        if receita is None and isinstance(preco, (int, float)) and isinstance(vendas, (int, float)):
            receita = round(preco * vendas, 2)            # estimativa: preço × vendas
        out.append({
            "produto": nome,
            "preco":  preco,
            "moeda":  _first(it, "currency", "currencyCode", "currencySymbol") or "",
            "vendas": vendas,
            "vendas_texto": _first(it, "soldText"),
            "receita_estimada": receita,
            "loja":   _first(it, "sellerName", "shopName", "shop", "seller", "storeName"),
            "rating": _first(it, "rating", "score", "stars"),
            "url":    _first(it, "productUrl", "url", "link", "productLink"),
        })
    return out

def filtrar_produtos(items, min_vendas=1, top=None):
    """Limpa o pull cru: exige venda >= min e preço, remove duplicados
    (mesmo título+loja) e ordena por vendas (desc). Corta lixo antes da curadoria."""
    vistos, out = set(), []
    for p in sorted(items, key=lambda x: -(x.get("vendas") or 0)):
        v = p.get("vendas")
        if not isinstance(v, (int, float)) or v < min_vendas: continue   # sem venda -> fora
        if p.get("preco") in (None, ""): continue                        # sem preço -> fora
        chave = ((p.get("produto") or "").strip().lower()[:60], (p.get("loja") or "").strip().lower())
        if chave in vistos: continue                                     # duplicado -> fora
        vistos.add(chave); out.append(p)
    return out[:top] if top else out

def mapear_busca_criadores(items, lang="pt", min_seg=0, max_seg=None, excluir=None):
    """Busca de vídeos por termo (produto) -> lista de CREATORS candidatos a
    referência do nicho. Agrega autores, filtra idioma + faixa de seguidores +
    exclui a própria pessoa, e ranqueia por relevância (frequência) e alcance."""
    ex = (excluir or "").lstrip("@").lower()
    ag = {}
    for it in items:
        am = it.get("authorMeta") or {}
        h = am.get("name")
        if not h: continue
        a = ag.setdefault(h, {"handle": h, "nome": am.get("nickName") or "", "seguidores": 0,
                              "videos": 0, "pt": 0, "exemplo": "",
                              "url": am.get("profileUrl") or f"https://www.tiktok.com/@{h}"})
        a["videos"] += 1
        a["seguidores"] = max(a["seguidores"], am.get("fans") or 0)
        if it.get("textLanguage") == "pt": a["pt"] += 1
        if not a["exemplo"]: a["exemplo"] = (it.get("text") or "")[:60]
    out = []
    for a in ag.values():
        if a["handle"].lower() == ex: continue                       # exclui a própria
        if lang == "pt" and a["pt"] == 0: continue                   # filtro de idioma
        if a["seguidores"] < min_seg: continue                       # faixa: piso
        if max_seg is not None and a["seguidores"] > max_seg: continue  # faixa: teto
        out.append(a)
    out.sort(key=lambda x: (-x["videos"], -x["seguidores"]))         # relevância, depois alcance
    return out

# --------------------------- CLI --------------------------------------------
def _arg_n(default):
    if "--n" in sys.argv:
        try: return int(sys.argv[sys.argv.index("--n") + 1])
        except Exception: pass
    return default

def _opt_int(flag):
    if flag in sys.argv:
        try: return int(sys.argv[sys.argv.index(flag) + 1])
        except Exception: pass
    return None

def _opt_str(flag):
    if flag in sys.argv:
        try: return sys.argv[sys.argv.index(flag) + 1]
        except Exception: pass
    return None

def _token():
    t = os.environ.get("APIFY_TOKEN")
    if not t: raise SystemExit("ERRO: defina APIFY_TOKEN no ambiente.")
    return t

AMOSTRA_PERFIL = [
    {"playCount": 7052, "diggCount": 533, "commentCount": 21, "shareCount": 40, "collectCount": 88,
     "text": "Como se preparar para as datas #tiktokshop #tiktokshopbr", "createTimeISO": "2026-07-19T12:00:00.000Z",
     "hashtags": [{"name": "tiktokshop"}, {"name": "tiktokshopbr"}], "videoMeta": {"duration": 98},
     "webVideoUrl": "https://www.tiktok.com/@frohethais/video/1",
     "authorMeta": {"name": "frohethais", "nickName": "Thais Frohe", "fans": 48200, "heart": 1200000, "verified": False, "signature": "Afiliada TikTok Shop"}},
    {"playCount": 2002, "diggCount": 180, "commentCount": 24, "shareCount": 15, "collectCount": 52,
     "text": "Ganchos visuais que funcionam #tiktokshop #ia", "createTimeISO": "2026-07-22T09:00:00.000Z",
     "hashtags": [{"name": "tiktokshop"}, {"name": "ia"}], "videoMeta": {"duration": 110},
     "webVideoUrl": "https://www.tiktok.com/@frohethais/video/2",
     "authorMeta": {"name": "frohethais", "nickName": "Thais Frohe", "fans": 48200, "heart": 1200000, "verified": False, "signature": "Afiliada TikTok Shop"}},
    {"playCount": 417, "diggCount": 33, "commentCount": 4, "shareCount": 2, "collectCount": 9,
     "text": "Bastidor do meu dashboard #thaisfrohe", "createTimeISO": "2026-07-25T18:00:00.000Z",
     "hashtags": [{"name": "thaisfrohe"}], "videoMeta": {"duration": 106},
     "webVideoUrl": "https://www.tiktok.com/@frohethais/video/3",
     "authorMeta": {"name": "frohethais", "nickName": "Thais Frohe", "fans": 48200, "heart": 1200000, "verified": False, "signature": "Afiliada TikTok Shop"}},
]
AMOSTRA_PRODUTOS = [
    {"title": "Sérum Vitamina C 30ml", "price": 39.9, "soldCount": 12000, "revenue": 478800, "shopName": "Beauty Brazil", "rating": 4.8, "url": "https://shop.tiktok.com/x"},
    {"productName": "Mini Batom Matte", "salePrice": 24.5, "sales": 8300, "shop": "MAC", "stars": 4.7},
]
AMOSTRA_BUSCA = [
    {"textLanguage": "pt", "text": "kit 8 pincéis", "authorMeta": {"name": "ref_a", "nickName": "A", "fans": 50000}},
    {"textLanguage": "pt", "text": "pincéis macrilan", "authorMeta": {"name": "ref_b", "nickName": "B", "fans": 800}},
    {"textLanguage": "es", "text": "brochas", "authorMeta": {"name": "ref_es", "nickName": "ES", "fans": 300000}},   # não-pt -> cai
    {"textLanguage": "pt", "text": "meus pincéis", "authorMeta": {"name": "pri.andrade50", "fans": 2006}},           # a própria -> cai
    {"textLanguage": "pt", "text": "pincel gigante", "authorMeta": {"name": "ref_big", "fans": 9000000}},            # fora da faixa -> cai
]

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "autotest":
        p = mapear_perfil(AMOSTRA_PERFIL)
        pr = mapear_produtos(AMOSTRA_PRODUTOS)
        assert p["handle"] == "frohethais" and p["seguidores"] == 48200, "perfil"
        assert p["views"]["media"] == round(st.mean([7052, 2002, 417])), "views"
        assert p["cadencia_semana"] > 0 and p["duracao_media"] == 105, "cadencia/dur"
        assert len(p["top_videos"]) == 3 and p["top_videos"][0]["views"] == 7052, "top"
        assert len(pr) == 2 and pr[0]["vendas"] == 12000 and pr[1]["preco"] == 24.5, "produtos"
        fp = filtrar_produtos(pr + [
            {"produto": "Lixo sem venda", "preco": 9.9, "vendas": None, "loja": "X"},
            {"produto": "Sérum Vitamina C 30ml", "preco": 39.9, "vendas": 5, "loja": "Beauty Brazil"},
        ])
        assert len(fp) == 2 and all(isinstance(x["vendas"], (int, float)) for x in fp), "filtro: sem venda cai"
        assert [x["produto"] for x in fp].count("Sérum Vitamina C 30ml") == 1, "filtro: dedupe"
        assert fp[0]["vendas"] >= fp[-1]["vendas"], "filtro: ordena por vendas"
        refs = mapear_busca_criadores(AMOSTRA_BUSCA, lang="pt", min_seg=100, max_seg=500000, excluir="@pri.andrade50")
        assert {r["handle"] for r in refs} == {"ref_a", "ref_b"}, "descoberta: pt + faixa + exclui a própria"
        assert refs[0]["seguidores"] == 50000, "descoberta: ordenação"
        print("AUTOTEST OK — mapeadores + filtro + descoberta válidos")
        print(json.dumps({"perfil": p, "produtos": pr}, ensure_ascii=False, indent=2)[:900])
        return
    if cmd == "perfil":
        alvo = sys.argv[2]; saida = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "perfil_analise.json"
        handle = re.sub(r"^@", "", alvo.rstrip("/").split("/")[-1])
        inp = {"profiles": [handle], "resultsPerPage": _arg_n(30),
               "profileScrapeSections": ["videos"], "profileSorting": "latest"}
        items = run_actor(ACTOR_PERFIL, inp, _token())
        raw = _opt_str("--save-raw")           # preserva o dataset CRU (base da análise profunda)
        if raw:
            json.dump(items, open(raw, "w"), ensure_ascii=False)
            print(f"cru salvo: {raw} — {len(items)} itens")
        data = mapear_perfil(items)
        json.dump(data, open(saida, "w"), ensure_ascii=False, indent=2)
        print(f"perfil salvo: {saida} — @{data['handle']} · {data.get('seguidores')} seguidores · {data['amostra']} vídeos")
        return
    if cmd == "produtos":
        termo = sys.argv[2]; saida = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "produtos.json"
        # input no schema do trakk/tiktok-shop-search-scraper (padrão); outro actor -> ajuste as chaves
        inp = {"keywords": [termo], "country_code": os.environ.get("APIFY_PAIS", "BR"),
               "maxItems": _arg_n(50), "mode": "fast", "sortBy": os.environ.get("APIFY_SORT", "best_sellers")}
        # Para dado BR real (BRL) o TikTok exige IP do país -> proxy residencial.
        # Defina APIFY_PROXY_COUNTRY=BR (precisa de proxy residencial no plano Apify).
        # Sem isso, o actor retorna o catálogo global (US/USD) como referência de categoria.
        pais_proxy = os.environ.get("APIFY_PROXY_COUNTRY")
        if pais_proxy:
            inp["proxyConfiguration"] = {
                "useApifyProxy": True,
                "apifyProxyGroups": [os.environ.get("APIFY_PROXY_GROUP", "RESIDENTIAL")],
                "apifyProxyCountry": pais_proxy,
            }
        items = run_actor(ACTOR_PRODUTOS, inp, _token())
        crus = mapear_produtos(items)
        data = filtrar_produtos(crus, min_vendas=int(os.environ.get("APIFY_MIN_VENDAS", "1")), top=_opt_int("--top"))
        json.dump(data, open(saida, "w"), ensure_ascii=False, indent=2)
        print(f"produtos salvos: {saida} — {len(data)} de {len(crus)} (filtrado: sem venda/preço + dedupe, ordenado por vendas)")
        return
    if cmd == "descobrir":
        termo = sys.argv[2]
        saida = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "referencias.json"
        # aceita VÁRIOS termos de categoria (separados por vírgula) e agrega:
        # quem recorre em várias buscas = mais central no nicho (= referência).
        termos = [t.strip() for t in termo.split(",") if t.strip()]
        n = _arg_n(20); items = []
        for t in termos:
            inp = {"searchQueries": [t], "resultsPerPage": n,
                   "shouldDownloadVideos": False, "shouldDownloadCovers": False}
            try: items += run_actor(ACTOR_PERFIL, inp, _token())
            except SystemExit as e: print(f">> aviso: busca '{t}' falhou: {e}", file=sys.stderr)
        lang = _opt_str("--lang") or os.environ.get("APIFY_LANG", "pt")
        refs = mapear_busca_criadores(items, lang=lang, min_seg=_opt_int("--min-seg") or 0,
                                      max_seg=_opt_int("--max-seg"), excluir=_opt_str("--excluir"))
        json.dump(refs, open(saida, "w"), ensure_ascii=False, indent=2)
        print(f"referências: {saida} — {len(refs)} creators ({lang}) de {len(items)} vídeos em {len(termos)} termo(s)")
        for r in refs[:20]:
            print(f"  @{r['handle']:<22} {r['seguidores']:>9,} seg | {r['videos']}x | {r['exemplo'][:36]}".replace(",", "."))
        return
    print(__doc__); sys.exit(2)

if __name__ == "__main__":
    main()
