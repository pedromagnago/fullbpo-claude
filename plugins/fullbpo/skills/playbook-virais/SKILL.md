---
name: playbook-virais
description: Frente 2 (Conteúdo) — playbook de viralização de um nicho. Varre perfis de referência, isola os vídeos que estouraram (alcance muito acima da mediana) e decodifica os ganchos/formatos que funcionam, pra replicar. Use para descobrir o que viraliza num nicho e montar referências acionáveis.
---

# Playbook de Virais (Frente 2 — Conteúdo)

Descobre **o que viraliza** num nicho e transforma em receita replicável. Em vez de estudar 1 vídeo, varre **vários perfis de referência**, isola os **outliers** (vídeos com alcance muito acima da mediana do próprio creator) e decodifica o padrão. Faz parte do produto de análise de creators (ver `PRODUTO-CREATORS.md`).

## Quando usar

Pedidos como "o que tá viralizando nesse nicho", "me dá referências de vídeo que funcionam", "monta um playbook de ganchos".

## Como fazer

1. **Coletar os perfis de referência** (base compartilhada):
   ```bash
   APIFY_TOKEN=... bash "${CLAUDE_PLUGIN_ROOT}/skills/coleta-apify/scripts/coletar_nicho.sh" \
     <slug> "@ref1" "@ref2" "@ref3" --n 30
   ```
2. **Isolar os virais (outliers):**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/playbook-virais/scripts/achar_virais.py" \
     "nicho_<slug>" --min-multiplo 5
   ```
   Gera `virais.json` e imprime o ranking (múltiplo da mediana · views · creator · título). Múltiplo alto = vídeo que fugiu muito da média do próprio perfil → é ali que mora a receita.
3. **Decodificar cada viral** com `assistir-video` (transcrição + frames) e escrever a leitura no formato do `estudo-de-video`: gancho, estrutura, e o **padrão que se repete** entre os virais do nicho (ex.: gancho de "erro de preço", empilhamento de valor, urgência).
4. **Entregar o playbook:** os ganchos/formatos recorrentes + exemplos, na voz da marca (`voz-da-marca`).

## Entrada / saída

- **Entrada:** pasta com N `perfil_analise.json` (do `coletar_nicho.sh`).
- **Saída:** `virais.json` (ranking de outliers) → insumo pra decodificação e pro playbook.

## A aprofundar (roadmap)

- Decodificar os outliers em lote e **sintetizar padrões recorrentes** de gancho/formato do nicho (não só 1 a 1).
- Coletar mais vídeos por perfil (hoje o corte usa os top vídeos do `perfil_analise.json`).
- Ranquear "ganchos que se repetem" e montar um relatório-playbook dedicado.

## Limites

- Dados públicos via Apify (estimativas). Uso pra referência/curadoria — não republicar conteúdo de terceiros como se fosse da FullBPO.
