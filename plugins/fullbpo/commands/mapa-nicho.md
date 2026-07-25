---
description: Frente 1 (TikTok Shop) — monta o mapa competitivo de um nicho comparando N perfis concorrentes (posicionamento, tração, produtos)
argument-hint: <slug> <@concorrente1> <@concorrente2> ... [--nicho "termo"]
---
Você vai montar o **mapa competitivo de um nicho** para a FullBPO (Frente 1 — TikTok Shop). Argumentos: `$ARGUMENTS`.

1. **Pré-requisito:** confirme `APIFY_TOKEN` no ambiente (não peça pra colar no chat).
2. **Coletar os perfis** do nicho:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/skills/coleta-apify/scripts/coletar_nicho.sh" $ARGUMENTS
   ```
3. **Montar o mapa:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/mapa-nicho/scripts/montar_mapa.py" "nicho_<slug>" "nicho_<slug>/mapa.html" --titulo "<nome do nicho>"
   ```
4. **Interpretar e entregar** (voz da marca): quem lidera cada eixo, quem está em ascensão (melhor vídeo ≫ mediana), lacunas de posicionamento e — se houver `produtos.json` — quais produtos o nicho empurra e onde há espaço. Detalhes e roadmap: skill `mapa-nicho` e `PRODUTO-CREATORS.md`.
