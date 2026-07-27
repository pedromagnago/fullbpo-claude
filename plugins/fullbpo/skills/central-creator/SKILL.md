---
name: central-creator
description: Junta todas as entregas de um creator (estratégia/Shop, dossiês, estudo de vídeo frame a frame, performance, painel de vendas) em UM ÚNICO HTML com abas — a "Central de Inteligência" do cliente. Use quando as análises já existem espalhadas em vários HTMLs e o cliente pede um painel único/organizado, um índice, ou "junta tudo num lugar só".
---

# Central de Inteligência do Creator

Monta **um único HTML com abas** que reúne todas as entregas de um creator, para o cliente não se perder entre vários arquivos. Cada peça entra **embutida e isolada** em `<iframe srcdoc>` — mantém o CSS, o tema e o JS de cada relatório sem colisão — e o **toggle de tema da Central propaga** para todas as abas. É a camada de cima do produto de creators (ver `PRODUTO-CREATORS.md`); não gera análise nova, **compõe** as que já existem.

## Quando usar

"Junta tudo num painel só", "quero um índice das análises do creator", "tô me perdendo nos arquivos", "monta a central/dashboard do cliente". Pré-requisito: os HTMLs das peças já existem (`montar_shop.py`, `montar_relatorio.py`, `montar_painel.py`, uma página de performance etc.).

## Como fazer

1. **Garanta as peças** (cada uma um HTML autocontido). Típico:
   - Estratégia/Shop → `mapa-nicho/montar_shop.py` (já traz os dossiês por perfil).
   - Estudo de vídeo frame a frame → `estudo-de-video/montar_relatorio.py`.
   - Painel de vendas → `painel-vendas/montar_painel.py` (real com CSV, ou exemplo como "modelo").
   - Visão geral e Performance → páginas autocontidas (ver nota abaixo).
2. **Escreva o `central.json`** (manifesto — esquema abaixo), listando as abas.
3. **Monte:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/central-creator/scripts/montar_central.py" \
     "<central.json>" "<Central_Cliente.html>"
   ```
4. **Revise e entregue** (regra de ouro FullBPO: revisão humana antes do cliente). Publique como 1 artifact / 1 arquivo.

## Esquema do `central.json`

```json
{
  "cliente": "Nome (Apelido)",
  "subtitulo": "@handle · Divisão Shop",
  "data": "DD/MM/AAAA",
  "resumo": "1 linha do que é a central (opcional)",
  "tabs": [
    {"id": "visao",  "label": "Visão geral",     "tipo": "embed", "src": "visao.html"},
    {"id": "shop",   "label": "Estratégia · Shop","tipo": "embed", "src": "shop.html"},
    {"id": "video",  "label": "Estudo de vídeo",  "tipo": "embed", "src": "relatorio.html"},
    {"id": "perf",   "label": "Performance",      "tipo": "embed", "src": "performance.html"},
    {"id": "vendas", "label": "Painel de vendas", "tipo": "embed", "src": "painel.html",
     "badge": "modelo", "nota": "Ativa com o CSV do Affiliate Center."},
    {"id": "tt",     "label": "Perfil no TikTok", "tipo": "link",  "href": "https://www.tiktok.com/@handle"}
  ]
}
```

- `tipo: "embed"` embute o HTML em `src` (caminho relativo à pasta do `central.json`). `tipo: "link"` vira um botão que abre `href` em nova aba.
- `badge` põe um selo na aba (ex.: "modelo", "sob demanda"); `nota` põe uma faixa no topo daquela aba.
- A **primeira aba** é a ativa ao abrir. Convém ser uma **Visão geral** (diagnóstico em 30s + cartões que lançam as outras abas).

### Lançador entre abas (opcional)

Qualquer peça embutida pode trocar a aba da Central mandando `postMessage` pro pai:
```js
parent.postMessage({fullbpo_goto: 'shop'}, '*');  // id da aba
```
A `visao.html` usa isso nos cartões "Abrir →".

## Notas

- **Tema:** a Central esconde o `.toggle` de cada peça (convenção FullBPO) e controla o tema de todas via `postMessage({fullbpo_tema})`. Todas as peças já respeitam `prefers-color-scheme`, então o padrão do SO também funciona.
- **Performance / Visão geral:** ainda não têm gerador dedicado no plugin — hoje são páginas autocontidas escritas por análise (mesmos tokens de design das outras). Candidatas a virar `montar_performance.py` (a partir do `perfil_analise.json`) e `montar_visao.py`.
- **Tamanho:** cada peça é embutida inteira (inclui os frames base64 do estudo de vídeo). Uma central típica fica em algumas centenas de KB — 1 arquivo, abre offline e no link compartilhável.
- **Não republicar** conteúdo de terceiros; material de curadoria/inteligência, uso interno/cliente.
