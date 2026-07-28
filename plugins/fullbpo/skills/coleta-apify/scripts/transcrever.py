#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# transcrever.py — puxa as LEGENDAS (subtitleLinks, WebVTT) de cada vídeo do
# dataset cru e extrai o GANCHO (primeiros ~3s, o que mais importa no TikTok)
# + o texto completo. O actor já entrega o link da legenda pronta — não precisa
# baixar/transcrever áudio (isso é o assistir-video, pra 1 vídeo a fundo).
#
# Uso:
#   python3 transcrever.py <raw.json> [transcricoes.json] [--top N] [--seg 3.0]
#
# Saída: lista [{url, views, titulo, tem_legenda, gancho, texto}]. Best-effort:
# vídeo sem legenda pt entra com tem_legenda=false. Respeita HTTPS_PROXY.
# ---------------------------------------------------------------------------
import sys, os, json, re, urllib.request, ssl

def _num(v, k):
    x = v.get(k); return x if isinstance(x, (int, float)) else 0

def _pick_link(v, prefer=("por", "pt")):
    sl = (v.get("videoMeta") or {}).get("subtitleLinks") or []
    if not sl: return None
    for want in prefer:
        for s in sl:
            if want in (s.get("language") or "").lower():
                return s.get("downloadLink")
    return sl[0].get("downloadLink")

def _fetch_vtt(url, timeout=25):
    ctx = ssl.create_default_context()
    ca = os.environ.get("CA_BUNDLE") or "/root/.ccr/ca-bundle.crt"
    try:
        if os.path.exists(ca): ctx.load_verify_locations(ca)
    except Exception: pass
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read().decode("utf-8", "replace")

_TS = re.compile(r"(\d\d):(\d\d):(\d\d)[.,](\d\d\d)\s*-->\s*(\d\d):(\d\d):(\d\d)")

def _parse_vtt(txt, hook_seg=3.0):
    """Devolve (gancho, texto_completo) a partir do WebVTT."""
    linhas, gancho, cur_start = [], [], None
    for ln in txt.splitlines():
        m = _TS.search(ln)
        if m:
            h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
            cur_start = h * 3600 + mi * 60 + s + ms / 1000
            continue
        ln = ln.strip()
        if not ln or ln == "WEBVTT" or ln.isdigit(): continue
        linhas.append(ln)
        if cur_start is not None and cur_start <= hook_seg:
            gancho.append(ln)
    return " ".join(gancho).strip(), " ".join(linhas).strip()

def transcrever(items, top=None, hook_seg=3.0):
    vids = [v for v in items if v.get("playCount") is not None]
    vids.sort(key=lambda v: -_num(v, "playCount"))
    if top: vids = vids[:top]
    out, ok = [], 0
    for v in vids:
        url = v.get("webVideoUrl") or v.get("url")
        rec = {"url": url, "views": _num(v, "playCount"),
               "titulo": (v.get("text") or "")[:80], "tem_legenda": False, "gancho": "", "texto": ""}
        link = _pick_link(v)
        if link:
            try:
                gancho, texto = _parse_vtt(_fetch_vtt(link), hook_seg)
                if texto:
                    rec.update(tem_legenda=True, gancho=gancho, texto=texto); ok += 1
            except Exception as e:
                rec["erro"] = str(e)[:80]
        out.append(rec)
    return out, ok

def main():
    a = sys.argv[1:]
    if not a:
        print("uso: transcrever.py <raw.json> [transcricoes.json] [--top N] [--seg 3.0]"); sys.exit(2)
    raw = a[0]
    saida = a[1] if len(a) > 1 and not a[1].startswith("-") else "transcricoes.json"
    top = int(a[a.index("--top") + 1]) if "--top" in a else None
    seg = float(a[a.index("--seg") + 1]) if "--seg" in a else 3.0
    items = json.load(open(raw))
    recs, ok = transcrever(items, top=top, hook_seg=seg)
    json.dump(recs, open(saida, "w"), ensure_ascii=False, indent=2)
    print(f"transcrições: {saida} — {ok}/{len(recs)} com legenda pt")

if __name__ == "__main__":
    main()
