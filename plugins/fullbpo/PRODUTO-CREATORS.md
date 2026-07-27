# FullBPO — Produto de Análise de Creators (TikTok)

Linha de produto interna pra avaliar creators/afiliados de TikTok. Organizada em **duas frentes**, sobre um mesmo **motor**.

## Motor (base, já pronto)

| Peça | Papel |
|---|---|
| `coleta-apify` | Camada de dados: perfil, vídeos e produtos via Apify → JSON normalizado |
| `assistir-video` | Transcrição + frames de um vídeo (frame a frame) |
| `estudo-de-video` | Relatório HTML de estudo de 1 perfil + 1 vídeo |
| `painel-vendas` | Dashboard de vendas (TikTok Shop) a partir de `vendas.json` |
| `central-creator` | **Camada de cima:** junta todas as entregas num HTML único com abas (a "Central" do cliente) |
| `/avaliar` | Orquestra a avaliação de 1 creator |

## Frente 1 — TikTok Shop (inteligência competitiva)

**Objetivo:** mapear o nicho, concorrentes lado a lado.
**Eixos de avaliação:** posicionamento · tração/vitalidade · uso de produtos.

- Skill: **`mapa-nicho`** · Comando: **`/mapa-nicho`**
- Fluxo: coletar **N perfis concorrentes** (+ produtos do nicho) → modelo de comparação → **mapa competitivo** (HTML).
- Base compartilhada: `coleta-apify/scripts/coletar_nicho.sh` (coleta multi-perfil).
- Status: **esqueleto** — comparador de perfis funcionando; produtos e o cruzamento "quem empurra o quê" a aprofundar.

## Frente 2 — Conteúdo (viralização + referências)

**Objetivo:** o que viraliza no nicho e como replicar.
**Foco:** viralização · referências de nicho.

- Skill: **`playbook-virais`** · Comando: **`/virais`**
- Fluxo: coletar **N perfis de referência** → isolar **vídeos outliers** (alcance ≫ mediana) → decodificar gancho/estrutura (`assistir-video`) → **playbook de virais**.
- Base compartilhada: `coleta-apify/scripts/coletar_nicho.sh` + `playbook-virais/scripts/achar_virais.py`.
- Status: **esqueleto** — detector de outliers funcionando; decodificação em lote + relatório a aprofundar.

## Base compartilhada

Hoje o `coleta-apify` puxa 1 perfil; as duas frentes precisam de vários. Fluxo:
1. **Descoberta** (`apify.py descobrir`): a partir do **produto do vídeo viral** (extraído do texto), acha as referências do nicho — filtra idioma (pt) + faixa de seguidores, sem hashtag nem @ manual. → `referencias.json`.
2. **Coleta** (`coletar_nicho.sh`): roda a coleta sobre a lista de handles → `nicho_<slug>/` com um `perfil_analise.json` por creator (+ `produtos.json` opcional). Os dois lados leem essa mesma pasta.

## Entrega unificada — a Central

As duas frentes geram vários HTMLs (estratégia, dossiês, estudo de vídeo frame a frame, performance, painel de vendas). A skill **`central-creator`** (`montar_central.py`) junta tudo num **único HTML com abas** — cada peça embutida e isolada, tema unificado — pra o cliente ter **uma casa só** e não se perder. É o entregável de topo: rode as frentes, depois monte a Central por cima.

## Próximos passos (a aprofundar)

- **Frente 1:** cruzar produtos × perfis (quem vende o quê, sobreposição, gaps); score de tração; faixa de preço/ângulo por concorrente.
- **Frente 2:** decodificar os outliers em lote e sintetizar padrões de gancho/formato recorrentes do nicho; ranquear "ganchos que se repetem".
- Comum: coletor multi-perfil com dado ao vivo (precisa de `APIFY_TOKEN`).
