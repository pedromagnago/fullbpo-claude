---
name: assistir-video
description: "Assistir" e transcrever um vídeo público a partir do link (TikTok, Instagram Reels, YouTube, Kwai, Shorts). Use quando alguém colar um link de vídeo e pedir para assistir, transcrever, resumir, analisar ou tirar insights — inclusive referência de conteúdo, concorrência e ganchos para criação de conteúdo da FullBPO.
---

# Assistir Vídeo (transcrição + leitura de tela)

O Claude não reproduz áudio nem vídeo. Esta skill contorna isso: baixa o vídeo público, extrai a **legenda/transcrição** (o que é falado) e alguns **frames** (o que aparece na tela) para o Claude ler e então **resumir e analisar em pt-BR**.

Serve para referência de conteúdo (o que criadores estão fazendo, ganchos, estrutura), concorrência e curadoria — **não** para republicar material de terceiros.

## Quando usar

Quando alguém colar um link de vídeo (TikTok, Instagram Reels/Stories, YouTube, YouTube Shorts, Kwai, Facebook) e pedir algo como "assiste esse vídeo", "transcreve", "resume", "o que ela fala aqui", "tira os ganchos", "analisa esse concorrente".

## Como fazer

1. **Rode o script** com a URL (aceita link encurtado tipo `vt.tiktok.com/...`):

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/skills/assistir-video/scripts/assistir_video.sh" "<URL>"
   ```

   O script instala o que faltar (`yt-dlp`, `ffmpeg`, e `faster-whisper` só se precisar), baixa metadados, legenda, o vídeo e extrai os frames. No final ele imprime um bloco `===== MANIFESTO =====` com os **caminhos absolutos** dos arquivos gerados.

2. **Leia os arquivos do manifesto** com a ferramenta Read:
   - `dados.txt` — autora, legenda/caption, hashtags, duração, views/likes/comentários.
   - `transcricao.txt` — o que é falado (legenda da plataforma ou transcrição por áudio).
   - `frames/frame_*.jpg` — leia **cada frame como imagem** para captar o que aparece na tela (textos, telas de app, números, produtos, cortes).

3. **Entregue a análise em pt-BR** seguindo a voz da marca FullBPO. Estrutura sugerida:
   - **Resumo (2–3 linhas):** do que trata o vídeo.
   - **O que aparece na tela:** telas, números, produtos, textos vistos nos frames.
   - **Transcrição / pontos-chave:** o que é dito, em bullets.
   - **Ganchos e estrutura:** abertura, desenvolvimento, CTA — o que faz funcionar.
   - **Insights acionáveis:** o que dá para aplicar no conteúdo/operação da FullBPO.
   - Cite a fonte da transcrição (legenda da plataforma vs. transcrição por áudio) para o time saber a confiabilidade.

## Opções e limites

- **Mais/menos frames:** terceiro argumento (padrão 6). Ex.: `... "<URL>" "" 10`.
- **Modelo de transcrição por áudio:** `WHISPER_MODEL=small bash ...` (padrão `base`; usado só quando não há legenda).
- **Vídeo que exige login/privado:** não funciona por link público. Só com cookies do navegador: `COOKIES_FROM=chrome bash ...` (rodando em máquina com o navegador logado). Não force nem tente burlar bloqueios.
- **Legenda automática** pode conter pequenos erros de reconhecimento; a transcrição por áudio idem. Sinalize quando algo parecer transcrição imperfeita.
- **Direitos:** use apenas como referência/curadoria interna. Não republicar conteúdo de terceiros como se fosse da FullBPO.
