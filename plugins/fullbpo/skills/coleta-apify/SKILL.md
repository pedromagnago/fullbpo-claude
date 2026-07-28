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
  perfil "@frohethais" perfil_analise.json --n 40 --save-raw perfil.raw.json
```
Gera `perfil_analise.json` (mesmo esquema do `coletar_perfil.sh`, **+ `seguidores`, `nome`, `bio`, `verificado`, `curtidas_totais`**).

> **Sempre passe `--save-raw`.** O `perfil_analise.json` é um **resumo** (~8 médias); o `--save-raw` preserva o **dataset cru** (dezenas de campos por vídeo: som/trilha, timestamp, duração, saves/shares individuais, legendas, menções, `ttSeller`…). É esse cru que alimenta a **análise profunda** abaixo. Sem ele, essa informação é perdida.

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

Acha as referências do nicho por busca + filtro, sem hashtag genérica nem @ manual. **Duas formas, conforme o objetivo:**

- **Referências (recomendado):** termos de **CATEGORIA** (vários, separados por vírgula) + **piso de seguidores alto** → creators **estabelecidos**. Quem recorre em vários termos = mais central no nicho.
  ```bash
  APIFY_TOKEN=... python3 "${CLAUDE_PLUGIN_ROOT}/skills/coleta-apify/scripts/apify.py" \
    descobrir "maquiagem,pincel de maquiagem,resenha de maquiagem" referencias.json \
    --min-seg 20000 --max-seg 5000000 --excluir "@cliente"
  ```
- **Concorrência direta:** o **produto específico do viral** → quem vende o mesmo item (pares, geralmente menores).

Fluxo interno: busca cada termo → agrega os autores → filtra **idioma (pt)** + **faixa de seguidores** + tira a cliente → ranqueia por **recorrência** (nº de termos) e alcance. Saída `referencias.json` → alimenta o `coletar_nicho.sh`. A busca do TikTok varia a cada run; o Claude cura a lista final. Ajuste a "altura" da referência com `--min-seg`/`--max-seg`.

## Avaliação completa (orquestrador)

Para rodar tudo de uma vez (perfil + vídeo + produtos → dossiê com `conteudo.json` pré-preenchido), use o comando **`/avaliar`** ou direto:
```bash
APIFY_TOKEN=... bash "${CLAUDE_PLUGIN_ROOT}/skills/coleta-apify/scripts/avaliar.sh" \
  "@handle" --video "<URL opcional>" --nicho "<termo opcional>"
```
`avaliar.sh` é **idempotente** (pula o que já coletou) e chama `montar_esqueleto.py`, que converte o `perfil_analise.json` num `conteudo.json` já preenchido com métricas/hashtags/top vídeos — sobra só o qualitativo (marcado como `TODO`) para o analista/Claude.

## Análise profunda (não jogar o cru fora)

O resumo (`perfil_analise.json`) colapsa tudo em médias — e **a média mente** quando há um viral isolado (ex.: média 570 vs mediana 90 views). A camada profunda extrai do **dataset cru** o que o resumo descarta:

1. **Motor** — `scripts/analise_profunda.py` consome o(s) `*.raw.json` e produz um dossiê rico por perfil + benchmark do nicho:
   ```bash
   # 1 perfil:
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/coleta-apify/scripts/analise_profunda.py" perfil.raw.json analise.json
   # nicho inteiro (cliente + concorrentes) num arquivo, com mediana do nicho:
   python3 ".../analise_profunda.py" --nicho pri.raw.json conc1.raw.json ... -o nicho.json
   ```
   Extrai: **distribuição honesta** (mediana, p25/p75/p90, outliers, % abaixo de 1k, `média/mediana`), **áudio** (som original vs trend, quais rendem), **melhor dia/hora** (fuso BR, com amostra mínima p/ não seguir outlier), **duração × views** (sweet spot + correlação), **taxas** save/share/comment por vídeo, **tendência** no tempo, **hashtags** que performam, **colabs** (@menções), **seller?** (`ttSeller`), **correlações** e a **tabela de todos os vídeos** — além de um `diagnostico` em bullets prontos.

2. **Ganchos** — `scripts/transcrever.py` puxa as legendas (WebVTT dos `subtitleLinks`) e extrai o **gancho (primeiros ~3s)** + texto de cada vídeo:
   ```bash
   python3 ".../transcrever.py" perfil.raw.json transcricoes.json [--top N]
   ```
   Cobertura depende da TikTok (só alguns vídeos têm legenda automática) — é best-effort. Para 1 vídeo a fundo (frame a frame + áudio), use a skill `assistir-video`/`estudo-de-video`.

3. **Relatório** — `scripts/montar_analise.py` renderiza a análise profunda de 1 handle como HTML autocontido (SVG inline, tema FullBPO), usando o resto do nicho como **benchmark real** e os ganchos transcritos:
   ```bash
   python3 ".../montar_analise.py" nicho.json analise.html --handle pri.andrade50 --transc-dir .
   ```
   Vira a aba **Performance** da `central-creator`. Todos os três têm `autotest` (`analise_profunda.py autotest`).

## Como se liga no resto

- `perfil_analise.json` → você escreve a seção **perfil** do `conteudo.json` (skill `estudo-de-video`).
- `produtos.json` → vira o **Radar de Produtos**; e, agregado por produto/fornecedor, ajuda a montar um `vendas.json` **estimado** (skill `painel-vendas`) para um creator/concorrente.
- Para o painel **exato** do próprio cliente (comissão, inelegíveis, fornecedores privados), a fonte continua sendo o **export do Affiliate Center** — scraping público traz estimativas de mercado, não o dado privado.

## Limites e cuidados

- **Custo:** cada run do actor consome créditos Apify. Use `--n` para limitar. Prefira runs por demanda, não em loop.
- **Estimativas:** dados de Shop de terceiros são **estimados** (vendas/GMV). Marque a `fonte` nos JSONs para o relatório/painel deixar isso claro.
- **ToS / dado público:** coletar apenas dados públicos, para curadoria e inteligência — não republicar conteúdo de terceiros como se fosse da FullBPO.
- **Robustez:** se um actor mudar o schema, ajuste o mapeador (`mapear_perfil` / `mapear_produtos`) — o `autotest` fixa o formato esperado.
