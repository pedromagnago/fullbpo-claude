#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# apify.py — adaptador Apify -> modelo normalizado da FullBPO.
# Roda um actor do Apify e mapeia a saída para os JSONs que os renderizadores
# consomem (perfil_analise.json / produtos.json).
#
# Uso:
#   APIFY_TOKEN=... python3 apify.py perfil <@handle|url> [saida.json] [--n 30]
#   APIFY_TOKEN=... python3 apify.py produtos "<palavra|url>" [saida.json] [--n 100]
#   python3 apify.py autotest        # testa os mapeadores em amostra (sem token/rede)
#
# Actors (sobrescreva por env se quiser outro):
#   APIFY_ACTOR_PERFIL   (padrão clockworks/tiktok-scraper)
#   APIFY_ACTOR_PRODUTOS (padrão trakk/tiktok-shop-search-scraper)
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
            nm = ("#" + h["name"]) if isinstance(h, dict) and h.get("name") else str(h)
            if nm and nm != "#": seen.add(nm.lower())
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
        out.append({
            "produto": nome,
            "preco":  _first(it, "price", "salePrice", "priceValue", "minPrice"),
            "vendas": _first(it, "soldCount", "sales", "salesCount", "sold", "orderCount"),
            "receita": _first(it, "revenue", "gmv", "estimatedRevenue", "salesAmount"),
            "loja":   _first(it, "shopName", "sellerName", "shop", "seller", "storeName"),
            "rating": _first(it, "rating", "score", "stars"),
            "url":    _first(it, "url", "productUrl", "link", "productLink"),
        })
    return out

# --------------------------- CLI --------------------------------------------
def _arg_n(default):
    if "--n" in sys.argv:
        try: return int(sys.argv[sys.argv.index("--n") + 1])
        except Exception: pass
    return default

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
        print("AUTOTEST OK — mapeadores válidos")
        print(json.dumps({"perfil": p, "produtos": pr}, ensure_ascii=False, indent=2)[:900])
        return
    if cmd == "perfil":
        alvo = sys.argv[2]; saida = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "perfil_analise.json"
        handle = re.sub(r"^@", "", alvo.rstrip("/").split("/")[-1])
        inp = {"profiles": [handle], "resultsPerPage": _arg_n(30),
               "profileScrapeSections": ["videos"], "profileSorting": "latest"}
        items = run_actor(ACTOR_PERFIL, inp, _token())
        data = mapear_perfil(items)
        json.dump(data, open(saida, "w"), ensure_ascii=False, indent=2)
        print(f"perfil salvo: {saida} — @{data['handle']} · {data.get('seguidores')} seguidores · {data['amostra']} vídeos")
        return
    if cmd == "produtos":
        termo = sys.argv[2]; saida = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "produtos.json"
        inp = {"searchQueries": [termo], "maxItems": _arg_n(100)} if not termo.startswith("http") else {"startUrls": [{"url": termo}]}
        items = run_actor(ACTOR_PRODUTOS, inp, _token())
        data = mapear_produtos(items)
        json.dump(data, open(saida, "w"), ensure_ascii=False, indent=2)
        print(f"produtos salvos: {saida} — {len(data)} itens")
        return
    print(__doc__); sys.exit(2)

if __name__ == "__main__":
    main()
