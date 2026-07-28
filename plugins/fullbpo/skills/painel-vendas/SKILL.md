---
name: painel-vendas
description: Gera o "Painel de Vendas" da FullBPO (afiliação/seller TikTok Shop) como dashboard HTML autocontido — GMV, comissão, Pareto de produtos, fornecedores, composição por status e "apostas". Use quando alguém pedir para montar/atualizar o painel de vendas de um creator ou loja de TikTok Shop a partir de dados (CSV do Affiliate Center ou API de terceiros).
---

# Painel de Vendas (TikTok Shop)

Monta o **dashboard de vendas** como HTML **autocontido** (gráficos em **SVG inline**, sem libs/CDN) — abre em qualquer navegador e imprime em PDF. É o primeiro pilar do produto de análise de creators da FullBPO.

Arquitetura: **adaptador de fonte → `vendas.json` (modelo normalizado) → renderizador**. O renderizador (`montar_painel.py`) é agnóstico à origem do dado.

## Quando usar

Pedidos como "monta o painel de vendas desse creator", "atualiza o dashboard do cliente com o mês X", "gera o painel a partir desse export do TikTok Shop".

## Como fazer

1. **Obter os dados e normalizar em `vendas.json`** (esquema abaixo). A fonte depende do caso:
   - **CSV do Affiliate/Seller Center** (números *exatos* do próprio cliente) → um adaptador lê o export e preenche o `vendas.json`.
   - **API de terceiros** (EchoTik / FastMoss / Kalodata) → dados *estimados* de mercado; servem para montar o painel de **qualquer creator/concorrente** e para o Radar de Produtos. Não trazem comissão/inelegíveis privados — só o CSV traz.
2. **Renderizar:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/painel-vendas/scripts/montar_painel.py" "<vendas.json>" "<painel.html>"
   ```
3. **Revisar e entregar** (regra de ouro FullBPO: revisão humana antes de ir ao cliente).

## Esquema do `vendas.json`

```json
{
  "cliente": "Nome/Loja", "handle": "@handle", "mes": "Junho/2026",
  "fonte": "CSV Affiliate Center | EchoTik | ...", "meta_gmv": 500000,
  "kpis": {"gmv": 458007, "comissao": 45297, "itens": 5983,
           "ticket": 76.55, "gmv_dia": 15267, "inelegivel_pct": 13.1},
  "gmv_diario": [{"dia": 1, "gmv": 15200}, {"dia": 2, "gmv": 16100}],
  "pareto": [{"produto": "Nome", "comissao": 5200}],
  "fornecedores": [{"nome": "MAC", "gmv": 59893, "com_padrao": 8.5, "com_ads": 12.0, "negociavel": false}],
  "status": {"liquidado": 453763, "pendente": 4244, "inelegivel": 73360},
  "apostas": [{"produto": "Nome", "gmv_esperado": 2728, "tag": "Novo"}]
}
```

- Valores monetários e contagens são **números** (o renderizador formata em BRL: `R$ 1.234,56`).
- `pareto` pode vir em qualquer ordem — o renderizador ordena e calcula o corte de 80%.
- `fornecedores[].negociavel: true` pinta a linha e marca "🟡 negociar".
- `tag` das apostas: `"Novo"` (verde) ou `"Acelerando"` (âmbar).
- Campos/seções ausentes são omitidos no painel.

### Modo "aguardando" (creator ainda sem vendas)

Para um creator que **ainda não vende pelo Shop**, não invente número (nem use painel de exemplo de outra pessoa — isso confunde o cliente). Use o modo honesto: identidade dele + estrutura + o **potencial real do nicho**.

```json
{
  "cliente": "Nome (Apelido)", "handle": "@handle", "mes": "Aguardando 1º relatório",
  "aguardando": true,
  "potencial": {"minha_mediana": 110, "mediana_nicho": 3492,
                "obs": "Fechar a distância de alcance é o que destrava a venda no Shop."}
}
```
Renderiza KPIs como "—", explica como o painel popula (passos do CSV) e mostra a barra **sua mediana vs. mediana do nicho** (dado real vindo do `analise_profunda.py`). Assim que houver o CSV do Affiliate Center, troque por um `vendas.json` normal. `passos` (lista) é opcional e sobrescreve os passos padrão.

## Contrato do adaptador (a construir por fonte)

Um adaptador é um script que produz o `vendas.json` acima. Para adicionar um:
- **CSV:** mapear as colunas do export → `kpis`, `gmv_diario`, `pareto`, `fornecedores`, `status`. Precisa de **um export real de exemplo** para fixar os nomes de coluna.
- **API de terceiros:** precisa de **API key** e do formato de resposta do provedor (EchoTik tem docs/SDK; FastMoss tem plano de API; Kalodata via Enterprise). Mapear a resposta → `vendas.json`.

> Enquanto não houver adaptador para a fonte escolhida, dá para preencher o `vendas.json` na mão (ou via Claude, lendo o export) e já renderizar o painel.

## Limites

- **Dados reais, sempre.** Não inventar número. Marcar claramente quando a fonte for *estimativa* de terceiros vs. dado *exato* do Affiliate Center (o campo `fonte` aparece no rodapé do painel).
- **Sem scraping direto do TikTok Shop** (ToS/quebra fácil) — usar API oficial, de terceiros, ou o export do próprio cliente.
