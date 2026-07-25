#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# achar_virais.py — Frente 2 (Conteúdo): varre os perfis de um nicho e isola
# os vídeos OUTLIERS (alcance muito acima da mediana do próprio creator) —
# os candidatos a "referência viral" pra decodificar depois com assistir-video.
#
# Uso:
#   achar_virais.py <pasta_nicho> [--min-multiplo 5] [--saida virais.json]
#   <pasta_nicho> = pasta com vários perfil_analise.json (do coletar_nicho.sh).
# ---------------------------------------------------------------------------
import sys, os, glob, json

def arg(flag, default):
    if flag in sys.argv:
        try: return sys.argv[sys.argv.index(flag)+1]
        except Exception: pass
    return default

def main():
    pos = [a for a in sys.argv[1:] if not a.startswith("--")]
    pasta = pos[0] if pos else "."
    mult_min = float(arg("--min-multiplo", "5"))
    saida = arg("--saida", os.path.join(pasta, "virais.json"))

    virais = []
    perfis = 0
    for f in sorted(glob.glob(os.path.join(pasta, "*.json"))):
        if os.path.basename(f) in ("produtos.json", "nicho.json", "virais.json"): continue
        try: d = json.load(open(f, encoding="utf-8"))
        except Exception: continue
        if not d.get("handle"): continue
        perfis += 1
        med = ((d.get("views") or {}).get("mediana")) or 0
        if med <= 0: med = 1
        for v in d.get("top_videos", []):
            views = v.get("views") or 0
            mult = round(views / med, 1)
            if mult >= mult_min:
                virais.append({
                    "handle": d.get("handle"), "nome": d.get("nome"),
                    "views": views, "mediana_do_perfil": med, "multiplo": mult,
                    "likes": v.get("likes"), "data": v.get("data"),
                    "titulo": v.get("titulo"), "url": v.get("url"),
                })
    virais.sort(key=lambda x: -x["multiplo"])
    json.dump(virais, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"Perfis lidos: {perfis} · outliers (≥{mult_min:g}× a mediana): {len(virais)}")
    print(f"salvo: {saida}\n")
    if virais:
        print(f'{"MÚLT":>6}  {"VIEWS":>8}  {"CREATOR":<18}  TÍTULO')
        print("-" * 78)
        for v in virais[:20]:
            print(f'{v["multiplo"]:>5.0f}x  {v["views"]:>8,}  @{(v["handle"] or "")[:16]:<17}  {(v["titulo"] or "")[:38]}'.replace(",", "."))
        print("\nPróximo passo: decodificar cada URL com assistir-video + estudo-de-video.")
    else:
        print("Nenhum outlier no corte atual — baixe --min-multiplo ou colete mais vídeos por perfil.")

if __name__ == "__main__":
    main()
