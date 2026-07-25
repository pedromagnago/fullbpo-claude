---
description: Frente 2 (Conteúdo) — encontra os vídeos que viralizaram num nicho e decodifica os ganchos/formatos pra replicar
argument-hint: <slug> <@ref1> <@ref2> ... [--min-multiplo 5]
---
Você vai montar o **playbook de virais** de um nicho para a FullBPO (Frente 2 — Conteúdo). Argumentos: `$ARGUMENTS`.

1. **Pré-requisito:** confirme `APIFY_TOKEN` no ambiente (não peça pra colar no chat).
2. **Coletar os perfis de referência:**
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/skills/coleta-apify/scripts/coletar_nicho.sh" $ARGUMENTS
   ```
3. **Isolar os outliers:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/playbook-virais/scripts/achar_virais.py" "nicho_<slug>" --min-multiplo 5
   ```
4. **Decodificar** cada viral com a skill `assistir-video` (transcrição + frames) e escrever a leitura no formato `estudo-de-video`: gancho, estrutura e **o padrão que se repete** entre os virais.
5. **Entregar o playbook** — ganchos e formatos recorrentes + exemplos, na voz da marca. Detalhes e roadmap: skill `playbook-virais` e `PRODUTO-CREATORS.md`.
