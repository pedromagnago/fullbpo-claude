---
description: Avaliação completa de um creator de TikTok — coleta perfil (Apify), vídeo de referência e produtos do nicho, e gera os entregáveis (relatório + radar)
argument-hint: <@handle> [--video URL] [--nicho "termo"] [--n N]
---
Você vai rodar uma **avaliação completa** de um creator de TikTok para a FullBPO, em pt-BR e na voz da marca. Argumentos recebidos: `$ARGUMENTS`.

## 1. Pré-requisito
Confirme que a variável `APIFY_TOKEN` está no ambiente (conta Apify da FullBPO). Se não estiver, peça ao usuário para defini-la (não peça para colar o token no chat) e pare aqui.

## 2. Coleta (orquestrador)
Rode:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/coleta-apify/scripts/avaliar.sh" $ARGUMENTS
```
Ele monta o dossiê em `avaliacao_<handle>_<data>/` com `perfil_analise.json`, opcionalmente `produtos.json` e `video/`, e um `conteudo.json` pré-preenchido (só faltam os campos `TODO`). É idempotente — não recoleta o que já existe.

## 3. Análise (é aqui que você agrega valor)
Leia o dossiê e **preencha os `TODO` do `conteudo.json`** seguindo a skill `estudo-de-video`:
- `resumo_executivo`, `perfil.leitura` e `insights` — interprete os números (lidere pela **mediana** de views; a média costuma vir distorcida por vídeos virais/fixados). Use a skill `voz-da-marca`.
- Se houver `video/`, monte a `video.timeline` frame a frame (leia os contact sheets e os frames nítidos, conforme `assistir-video`).

## 4. Entregáveis
- **Relatório HTML:**
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/estudo-de-video/scripts/montar_relatorio.py" "<dossiê>/conteudo.json" "<dossiê>/relatorio.html"
  ```
- **Radar de produtos** (se houver `produtos.json`): rankeie por `receita_estimada`/`vendas` e destaque os virais do nicho (produtos com potencial de pauta).
- **Painel de vendas exato** do cliente: só com o export do Affiliate Center → `vendas.json` → skill `painel-vendas`. Deixe claro quando o dado for estimativa de terceiros vs. exato.

## 5. Fechamento
Entregue os arquivos ao usuário e um resumo do que foi encontrado. Lembre que todo material passa por **revisão humana antes de ir ao cliente**.
