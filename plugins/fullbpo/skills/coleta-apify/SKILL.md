---
name: coleta-apify
description: Coleta dados públicos de TikTok e TikTok Shop via Apify (actors) e converte para os modelos normalizados da FullBPO (perfil_analise.json, produtos.json). Use quando precisar puxar métricas de um perfil/creator, benchmark de concorrentes ou produtos virais do TikTok Shop para alimentar as skills painel-vendas e estudo-de-video.
---

# Coleta via Apify (TikTok / TikTok Shop)

Camada de **dados** do produto de análise de creators. Roda um **actor do Apify** e mapeia a saída para o JSON normalizado que os renderizadores consomem — mantendo a arquitetura **fonte → modelo → renderizador**.

Script: `scripts/apify.py` (só stdlib; respeita `HTTPS_PROXY` e o CA do ambiente).

## Pré-requisitos

- **`APIFY_TOKEN`** no ambiente (conta Apify da FullBPO).
- Actors (sobrescreva por env se usar outro):
  - `APIFY_ACTOR_PERFIL` — padrão **`clockworks/tiktok-scraper`** (perfil, vídeos, seguidores).
  - `APIFY_ACTOR_PRODUTOS` — padrão **`trakk/tiktok-shop-search-scraper`** (produtos/preços/vendas). Há vários actors de Shop; o mapeador é tolerante a nomes de campo, mas confira a saída do actor escolhido.

## Como usar

**Perfil / conteúdo** (alimenta `estudo-de-video` e o benchmark de concorrentes):
```bash
APIFY_TOKEN=... python3 "${CLAUDE_PLUGIN_ROOT}/skills/coleta-apify/scripts/apify.py" \
  perfil "@frohethais" perfil_analise.json --n 30
```
Gera `perfil_analise.json` (mesmo esquema do `coletar_perfil.sh`, **+ `seguidores`, `nome`, `bio`, `verificado`, `curtidas_totais`**).

**Produtos / TikTok Shop** (alimenta o Radar de Produtos e painéis estimados):
```bash
APIFY_TOKEN=... python3 "${CLAUDE_PLUGIN_ROOT}/skills/coleta-apify/scripts/apify.py" \
  produtos "sérum vitamina c" produtos.json --n 100
# ou uma URL de categoria/loja/produto do TikTok Shop no lugar da palavra-chave
```
Gera `produtos.json` — lista normalizada: `produto, preco, vendas, receita, loja, rating, url`. O pull **já vem filtrado**: descarta produto sem venda, sem preço e duplicado (mesmo título+loja), ordenado por vendas (desc). Ajuste com `APIFY_MIN_VENDAS` (padrão 1) e `--top N`. Depois disso, o Claude ainda cura o que entra no relatório.

> **Dado BR (BRL):** o TikTok só serve o catálogo brasileiro pra um **IP do Brasil**. Sem isso, o actor retorna o catálogo **global (US/USD)** — útil como referência de categoria, mas não é o preço/oferta BR. Para dado BR real, rode com **proxy residencial BR**:
> ```bash
> APIFY_PROXY_COUNTRY=BR APIFY_TOKEN=... python3 .../apify.py produtos "pincel de maquiagem" produtos.json
> ```
> Isso exige **proxy residencial** habilitado no plano Apify (add-on pago) — no plano FREE o resultado volta vazio ou global. Enquanto não houver, trate os produtos como sinal de categoria e cruze com o que os concorrentes **BR** já vendem nos vídeos.

**Autoteste** (valida os mapeadores sem token/rede):
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/coleta-apify/scripts/apify.py" autotest
```

## Descoberta de nicho (referências — sem hashtag/@)

Acha as **referências do nicho** ancorando no **produto do vídeo viral** (que o Claude extrai do texto/transcrição do vídeo), sem hashtag genérica nem lista manual de @:
```bash
APIFY_TOKEN=... python3 "${CLAUDE_PLUGIN_ROOT}/skills/coleta-apify/scripts/apify.py" \
  descobrir "<produto do viral>" referencias.json --min-seg 500 --max-seg 300000 --excluir "@cliente"
```
Busca o produto → agrega os autores dos vídeos → filtra **idioma (pt)** + **faixa de seguidores** + tira a própria cliente → ranqueia por relevância/alcance. Saída `referencias.json` (handles) alimenta o `coletar_nicho.sh`. Dica: a busca do TikTok varia a cada run — rode com **termos variados do mesmo produto** pra ampliar a cobertura, e o Claude cura a lista final.

## Avaliação completa (orquestrador)

Para rodar tudo de uma vez (perfil + vídeo + produtos → dossiê com `conteudo.json` pré-preenchido), use o comando **`/avaliar`** ou direto:
```bash
APIFY_TOKEN=... bash "${CLAUDE_PLUGIN_ROOT}/skills/coleta-apify/scripts/avaliar.sh" \
  "@handle" --video "<URL opcional>" --nicho "<termo opcional>"
```
`avaliar.sh` é **idempotente** (pula o que já coletou) e chama `montar_esqueleto.py`, que converte o `perfil_analise.json` num `conteudo.json` já preenchido com métricas/hashtags/top vídeos — sobra só o qualitativo (marcado como `TODO`) para o analista/Claude.

## Como se liga no resto

- `perfil_analise.json` → você escreve a seção **perfil** do `conteudo.json` (skill `estudo-de-video`).
- `produtos.json` → vira o **Radar de Produtos**; e, agregado por produto/fornecedor, ajuda a montar um `vendas.json` **estimado** (skill `painel-vendas`) para um creator/concorrente.
- Para o painel **exato** do próprio cliente (comissão, inelegíveis, fornecedores privados), a fonte continua sendo o **export do Affiliate Center** — scraping público traz estimativas de mercado, não o dado privado.

## Limites e cuidados

- **Custo:** cada run do actor consome créditos Apify. Use `--n` para limitar. Prefira runs por demanda, não em loop.
- **Estimativas:** dados de Shop de terceiros são **estimados** (vendas/GMV). Marque a `fonte` nos JSONs para o relatório/painel deixar isso claro.
- **ToS / dado público:** coletar apenas dados públicos, para curadoria e inteligência — não republicar conteúdo de terceiros como se fosse da FullBPO.
- **Robustez:** se um actor mudar o schema, ajuste o mapeador (`mapear_perfil` / `mapear_produtos`) — o `autotest` fixa o formato esperado.
