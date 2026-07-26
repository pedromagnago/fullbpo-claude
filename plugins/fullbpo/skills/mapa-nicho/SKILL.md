---
name: mapa-nicho
description: Frente 1 (TikTok Shop) — mapa competitivo de um nicho. Coleta e compara N perfis concorrentes lado a lado (posicionamento, tração/vitalidade e uso de produtos) e gera um dashboard HTML. Use para avaliar concorrência, posicionamento e produtos de um nicho de afiliação/seller no TikTok.
---

# Mapa Competitivo do Nicho (Frente 1 — TikTok Shop)

Compara **vários concorrentes** de um nicho lado a lado, em 3 eixos: **posicionamento** (bio, categorias, ângulo), **tração/vitalidade** (seguidores, mediana de views, engajamento, melhor vídeo, cadência) e **uso de produtos** (o que cada um empurra — a aprofundar). Faz parte do produto de análise de creators (ver `PRODUTO-CREATORS.md`).

## Quando usar

Pedidos como "compara esses perfis do nicho", "mapa da concorrência de X", "quem tá crescendo nesse nicho e vendendo o quê".

## Como fazer

1. **Coletar os perfis do nicho** (base compartilhada):
   ```bash
   APIFY_TOKEN=... bash "${CLAUDE_PLUGIN_ROOT}/skills/coleta-apify/scripts/coletar_nicho.sh" \
     <slug> "@concorrente1" "@concorrente2" "@concorrente3" --nicho "<termo de produto>"
   ```
   Gera `nicho_<slug>/` com um `perfil_analise.json` por creator (+ `produtos.json` se `--nicho`).
2. **Montar o mapa:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/mapa-nicho/scripts/montar_mapa.py" \
     "nicho_<slug>" "nicho_<slug>/mapa.html" --titulo "Nicho X"
   ```
   Tabela de tração com o **líder de cada métrica destacado** + cards de posicionamento (bio + hashtags).
3. **Ler e interpretar** (o valor está aqui): quem lidera cada eixo, quem tá em ascensão (melhor vídeo ≫ mediana = teto alto), lacunas de posicionamento, e — com `produtos.json` — quais produtos o nicho empurra e onde há espaço. Escreva a leitura na voz da marca (`voz-da-marca`).

## Entrada / saída

- **Entrada:** pasta com N `perfil_analise.json` (do `coletar_nicho.sh`) + opcional `produtos.json`.
- **Saída:** `mapa.html` autocontido, tema claro/escuro, imprime em PDF.

## Entregável principal: dash centrado no creator (`montar_shop.py`)

O `montar_mapa.py` acima compara N perfis de forma simétrica. Mas o entregável do cliente é **centrado em 1 creator-alvo** (ex.: a cliente) — os concorrentes e o nicho entram como munição. Use `montar_shop.py`:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/mapa-nicho/scripts/montar_shop.py" "<shop.json>" "<saida.html>"
```

Ele monta um dash que responde, **para a cliente**: onde ela está · **como a concorrência viraliza** · **quais vídeos do nicho viralizaram** · **quais produtos vendem bem e ela pode adotar** · recomendações. Você escreve o `shop.json` juntando: o perfil dela, os concorrentes (`perfil_analise.json`), os virais (`achar_virais.py` da Frente 2) e os produtos (`coleta-apify produtos`).

Esquema do `shop.json`:
```json
{
  "cliente": "Nome — Divisão Shop", "data": "DD/MM/AAAA",
  "subject": {"handle":"…","nome":"…","seguidores":0,"mediana":0,"engajamento":0,"cadencia":0,"melhor":0,"duracao":0,
              "viral": {"titulo":"…","views":0,"multiplo":0,"url":"…"}},
  "resumo": ["…"],
  "concorrentes": [{"handle":"…","nome":"…","seguidores":0,"mediana":0,"engajamento":0,"melhor":0,"como_viraliza":"…"}],
  "virais_nicho": [{"handle":"…","multiplo":0,"views":0,"titulo":"…","url":"…"}],
  "padrao_virais": "o que os virais têm em comum…",
  "produtos_nicho": [{"produto":"…","vendas":0,"preco":"…","moeda":"USD","loja":"…"}],
  "produtos_nota": "fonte + caveat de região (BR vs global)…",
  "recomendacoes": [{"titulo":"…","texto":"…"}]
}
```
Texto aceita `**negrito**` e `*itálico*`.

> Nota de dados: o actor de produtos padrão retorna **mercado global (USD)** mesmo com `country_code=BR` — trate os produtos como sinal de categoria e valide fornecedor/disponibilidade BR (deixe claro no `produtos_nota`).

## A aprofundar (roadmap)

- Cruzar `produtos.json` × perfis: quem vende o quê, sobreposição de catálogo, campeões e gaps do nicho.
- Score de tração e faixa de preço/ângulo por concorrente.
- Coleta ao vivo em lote (precisa de `APIFY_TOKEN`).

## Limites

- Dados públicos via Apify são **estimativas de mercado** — bom pra comparação relativa, não pro número privado de cada um. Uso interno/curadoria; não republicar conteúdo de terceiros.
