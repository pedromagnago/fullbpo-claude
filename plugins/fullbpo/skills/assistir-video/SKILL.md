---
name: assistir-video
description: Assistir, resumir ou transcrever um vídeo que chegou na operação — Reel/Story do Instagram, YouTube, TikTok, vídeo de WhatsApp, link .mp4 ou arquivo local. Use sempre que o usuário mandar um link/arquivo de vídeo e pedir para você ver, resumir, transcrever ou extrair o conteúdo. Roda 100% local (bom para material sigiloso de cliente).
---

# Assistir Vídeo

O Claude não processa vídeo direto, mas **lê imagens**. Esta skill quebra o vídeo em
frames (imagens) que você lê com a ferramenta `Read` e, se precisar, transcreve o
áudio — tudo local, sem mandar o conteúdo para serviço externo.

## Como usar

1. **Rode o script** com a URL ou o caminho do arquivo:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/assistir-video/ver_video.py" "<url-ou-arquivo>"
   ```

   Ele baixa (se for URL), extrai ~30 frames e o áudio, e imprime um **manifesto**
   com a pasta de saída e a lista de frames.

2. **Leia os frames** listados no manifesto com a ferramenta `Read` (uma leitura
   por imagem, ou várias em paralelo). É assim que você "vê" o vídeo — legendas
   queimadas, telas, slides e o que aparece na cena.

3. **Resuma** para o usuário: do que trata, pontos principais, e o que ele pediu.

## Opções

- `--transcrever` — além dos frames, transcreve a fala (faster-whisper, local).
  Use quando o vídeo é mais "falado" que visual, ou quando as legendas não bastam.
- `--frames N` — nº aproximado de frames (padrão 30). Vídeo longo com muito texto
  na tela? Aumente. Clipe curto? Diminui.
- `--out PASTA` — pasta de saída (padrão: uma pasta temporária).

Exemplo completo:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/assistir-video/ver_video.py" \
  "https://www.instagram.com/reel/XXXX/" --frames 40 --transcrever
```

## Requisitos

Instalados automaticamente na primeira vez (via pip): `yt-dlp` e `imageio-ffmpeg`
(traz o binário do ffmpeg embutido, não precisa instalar ffmpeg no sistema). O
`--transcrever` baixa um modelo de ~140 MB do faster-whisper na primeira vez.

## Limites e boas práticas

- **Conteúdo com login** (perfil privado, vídeo restrito) pode não baixar. Se der
  erro de acesso, peça o arquivo direto ou uma gravação de tela.
- **Vídeo longo** (aula, reunião): 30 frames dão o panorama; para pegar texto de
  tela use `--frames` maior, e para a fala completa use `--transcrever`.
- **Sigilo:** o pipeline é 100% local — nada do vídeo sai da máquina. Ainda assim,
  material de cliente é confidencial: não suba frames nem transcrição para fora do
  escopo da pasta do cliente, seguindo as regras do `metodo-fullbpo`.
- **Limpeza:** a pasta de saída é temporária; apague depois de resumir se o vídeo
  for sensível.
