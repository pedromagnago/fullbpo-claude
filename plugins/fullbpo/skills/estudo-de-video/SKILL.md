---
name: estudo-de-video
description: Gera um relatório HTML de "estudo de vídeo + perfil" como entrega ao cliente. Use quando alguém pedir um estudo/análise de um vídeo de referência (TikTok, Reels, YouTube, Shorts) com análise também do perfil do criador — para curadoria, concorrência e pauta de conteúdo. Produz um HTML padrão FullBPO, autocontido, com a linha do tempo frame a frame e as imagens do vídeo.
---

# Estudo de Vídeo & Perfil (relatório HTML ao cliente)

Transforma um link de vídeo num **relatório HTML padrão da FullBPO** para entregar ao cliente: analisa **o perfil** do criador (métricas reais) **e o vídeo** (linha do tempo frame a frame, com as imagens da tela) e fecha com **recomendações acionáveis**.

O HTML é **autocontido** (CSS inline, imagens em base64) — um único arquivo que o cliente abre em qualquer navegador ou salva em PDF. Depende da skill `assistir-video` para a parte do vídeo.

## Quando usar

Quando o pedido for um **estudo/análise entregável** de um vídeo de referência — não só "resume esse vídeo" (aí use `assistir-video`), mas "faz um estudo desse vídeo e do perfil pra eu mandar", "análise de concorrente", "quero um relatório desse criador".

## Fluxo

1. **Coletar o vídeo** (frames + transcrição + dados) — via a skill `assistir-video`:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/skills/assistir-video/scripts/assistir_video.sh" "<URL_do_video>" "<pasta_trabalho>"
   ```
2. **Coletar o perfil** (métricas dos vídeos recentes):
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/skills/estudo-de-video/scripts/coletar_perfil.sh" "<URL_do_perfil>" "<pasta_trabalho>"
   ```
   Gera `perfil_analise.json` (views/engajamento/cadência/hashtags/top vídeos).
3. **Assistir e analisar** (é aqui que entra o julgamento):
   - Leia os **contact sheets** e depois os **frames individuais** nítidos (sem a mão na frente) das telas que importam — leia os números direto do frame.
   - Leia `transcricao.txt` (com timestamps) e `dados.txt`.
   - Leia `perfil_analise.json` e interprete (não repita número cru — diga o que significa).
4. **Escrever o `conteudo.json`** (esquema abaixo), curando **6 a 9 frames** para a linha do tempo — priorize as telas de maior valor (números, gráficos, listas), não frames de "cabeça falante" repetidos.
5. **Montar o HTML**:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/estudo-de-video/scripts/montar_relatorio.py" "<pasta_trabalho>/conteudo.json" "<pasta_trabalho>/relatorio.html"
   ```
6. **Revisar e entregar.** Confira o HTML (abra/rende). Todo entregável passa por **revisão humana antes de ir ao cliente** (regra de ouro FullBPO).

## Esquema do `conteudo.json`

Texto aceita **`**negrito**`** e **`*itálico*`**. Campos opcionais podem ser omitidos (a seção some).

```json
{
  "cliente": "Nome do cliente",
  "data": "DD/MM/AAAA",
  "analista": "FullBPO — Backoffice Inteligente",
  "objeto": {
    "autora": "Nome do criador", "handle": "@handle",
    "video_url": "https://…", "perfil_url": "https://…",
    "video_stats": {"views":"2.492","likes":"230","comentarios":"36","compart":"69","duracao":"1min46","publicado":"DD/MM/AAAA"}
  },
  "resumo_executivo": ["parágrafo 1", "parágrafo 2"],
  "perfil": {
    "metricas": [{"rotulo":"Views por vídeo (média)","valor":"2.552","nota":"mediana 2.002"}],
    "hashtags": [["#tiktokshop", 32]],
    "top_videos": [{"views":"7.052","likes":"533","data":"DD/MM/AAAA","titulo":"…"}],
    "leitura": ["análise textual do perfil (o que os números dizem)…"]
  },
  "video": {
    "gancho": "por que a abertura funciona…",
    "estrutura": "como o vídeo é construído…",
    "timeline": [
      {"t":"0–10s","frame":"frame_001_t0000.0s.jpg","tela":"o que aparece na tela","fala":"o que é dito"}
    ]
  },
  "insights": [{"titulo":"…","texto":"…"}],
  "metodologia": "fontes e método (transcrição, amostra do perfil, frames)…",
  "frames_dir": "/caminho/absoluto/para/<pasta_trabalho>/frames"
}
```

- **`timeline[].frame`** é o nome do arquivo dentro de `frames_dir` (veja `frames/index.txt`). Entradas **sem** `frame` viram um bloco de texto (bom para beats curtos entre telas).
- `metricas` e `video_stats` são strings já formatadas em pt-BR (use `.` de milhar e `,` decimal).

## Limites e cuidados

- **Dados reais, sempre.** As métricas de perfil vêm do `perfil_analise.json`; os números do dashboard, dos frames. Não invente número — se não conseguir ler, omita ou marque como estimativa.
- **Voz da marca** (skill `voz-da-marca`): direta, sem jargão, todo insight termina em decisão.
- **Confidencialidade e direitos:** o conteúdo analisado é público e de terceiros; o relatório é **curadoria/inteligência**, não republicação. O rodapé já traz esse aviso. Não use para copiar/republicar conteúdo alheio como se fosse da FullBPO.
- **Perfil privado/bloqueado:** a coleta não funciona por link público; não tente burlar.
