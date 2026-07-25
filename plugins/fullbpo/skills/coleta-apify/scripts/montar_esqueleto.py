#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# montar_esqueleto.py — a partir do perfil_analise.json (e, se houver, do
# vídeo coletado), gera um conteudo.json PRÉ-PREENCHIDO para a skill
# estudo-de-video. O trabalho braçal (métricas, hashtags, top vídeos) já vem
# dos dados reais; o Claude só escreve o qualitativo (marcado como TODO).
#
# Uso: montar_esqueleto.py <perfil_analise.json> <pasta_trabalho>
# ---------------------------------------------------------------------------
import sys, os, json
from datetime import date  # date.today() não é permitido no sandbox de workflow, mas aqui é CLI normal

def bi(n):
    try: return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError): return str(n)

def main():
    if len(sys.argv) < 3:
        print("uso: montar_esqueleto.py <perfil_analise.json> <pasta_trabalho>", file=sys.stderr); sys.exit(2)
    p = json.load(open(sys.argv[1], encoding="utf-8"))
    work = sys.argv[2]
    handle = p.get("handle", "")
    v = p.get("views", {})

    # objeto + eventual vídeo coletado
    objeto = {"autora": p.get("nome") or handle, "handle": f"@{handle}" if handle else "",
              "perfil_url": f"https://www.tiktok.com/@{handle}" if handle else ""}
    video_block = None
    dados_path = os.path.join(work, "video", "dados.txt")
    frames_dir = os.path.join(work, "video", "frames")
    if os.path.isfile(dados_path):
        dd = {}
        for ln in open(dados_path, encoding="utf-8", errors="ignore"):
            if ":" in ln:
                key, _, val = ln.partition(":"); dd[key.strip()] = val.strip()
        objeto["video_url"] = dd.get("webpage_url", "")
        objeto["video_stats"] = {"views": bi(dd.get("view_count")), "likes": bi(dd.get("like_count")),
                                 "comentarios": bi(dd.get("comment_count")), "compart": bi(dd.get("repost_count")),
                                 "publicado": dd.get("upload_date", "")}
        video_block = {
            "gancho": "TODO — por que a abertura funciona (leia os primeiros frames + transcrição).",
            "estrutura": "TODO — como o vídeo é construído (ritmo, blocos, CTA).",
            "timeline": []  # TODO — montar frame a frame lendo os contact sheets/frames (ver estudo-de-video)
        }

    # métricas do perfil — LIDERA PELA MEDIANA (média é distorcida por virais/pinned)
    metricas = [
        {"rotulo": "Seguidores", "valor": bi(p.get("seguidores")), "nota": f'{bi(p.get("curtidas_totais"))} curtidas totais' if p.get("curtidas_totais") else ""},
        {"rotulo": "Views por vídeo (mediana)", "valor": bi(v.get("mediana")), "nota": f'média {bi(v.get("media"))} · máx {bi(v.get("max"))}'},
        {"rotulo": "Engajamento (proxy)", "valor": f'{str(p.get("engajamento_proxy","")).replace(".", ",")}%', "nota": "interações ÷ views"},
        {"rotulo": "Cadência", "valor": f'{str(p.get("cadencia_semana","")).replace(".", ",")}/sem', "nota": f'{p.get("amostra")} vídeos · {" a ".join(p.get("periodo",["",""]))}'},
        {"rotulo": "Salvos por vídeo", "valor": bi(p.get("saves_media")), "nota": "sinal de conteúdo de referência"},
        {"rotulo": "Duração média", "valor": f'{p.get("duracao_media")}s', "nota": ""},
    ]
    top_videos = [{"views": bi(t.get("views")), "likes": bi(t.get("likes")),
                   "data": t.get("data", ""), "titulo": t.get("titulo", "")} for t in p.get("top_videos", [])]

    leitura_todo = (f'TODO — leitura do perfil. Contexto: @{handle} tem {bi(p.get("seguidores"))} seguidores, '
                    f'mediana de {bi(v.get("mediana"))} views (média {bi(v.get("media"))} puxada por viral de {bi(v.get("max"))}), '
                    f'engajamento {p.get("engajamento_proxy")}%, cadência {p.get("cadencia_semana")}/sem, '
                    f'{bi(p.get("saves_media"))} salvos/vídeo. Bio: "{p.get("bio","")}". '
                    f'Diga o que isso significa (nicho, posicionamento, o que vende).')

    conteudo = {
        "cliente": "TODO — nome do cliente",
        "data": date.today().strftime("%d/%m/%Y"),
        "analista": "FullBPO — Backoffice Inteligente",
        "objeto": objeto,
        "resumo_executivo": ["TODO — resumo executivo (2 parágrafos): quem é, o que o material mostra, e o take estratégico."],
        "perfil": {
            "metricas": metricas,
            "hashtags": p.get("top_hashtags", []),
            "top_videos": top_videos,
            "leitura": [leitura_todo],
        },
        "insights": [{"titulo": "TODO — recomendação", "texto": "TODO — o que aplicar no conteúdo/operação da FullBPO."}],
        "metodologia": (f'Perfil via Apify (clockworks/tiktok-scraper), {p.get("amostra")} vídeos '
                        f'({" a ".join(p.get("periodo",["",""]))}). Métricas estimadas de dados públicos.'),
    }
    if video_block:
        conteudo["video"] = video_block
        conteudo["frames_dir"] = frames_dir
        conteudo["metodologia"] += " Vídeo: transcrição + frames (skill assistir-video)."

    out = os.path.join(work, "conteudo.json")
    json.dump(conteudo, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"esqueleto salvo: {out} — preencha os campos TODO e rode a skill estudo-de-video")

if __name__ == "__main__":
    main()
