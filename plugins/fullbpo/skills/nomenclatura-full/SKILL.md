---
name: nomenclatura-full
description: Convenções de nomenclatura de arquivos da FullBPO. Use ao criar ou salvar qualquer arquivo na pasta de um cliente (relatórios, conciliações, decks de mentoria).
---

# Nomenclatura de Arquivos FullBPO

Ao criar arquivo novo, seguir o padrão observado na operação:

- **Relatórios:** `[CLIENTE] - [TIPO] - [MM_AAAA].xlsx`
  Ex: `JUMA - DRE Gerencial - 04_2026.xlsx`
- **Conferências:** `Conferencia_[Lançamentos|Pagamentos]_[MM_AAAA].xlsx`
  Ex: `Conferencia_Lancamentos_04_2026.xlsx`
- **Conciliações:** `Conciliacao_[Banco|Cartao|Fornecedores|Clientes]_[MM_AAAA].xlsx`
- **Decks de mentoria:** `Mentoria_[CLIENTE]_[MM_AAAA].pptx`
  Ex: `Mentoria_JUMA_04_2026.pptx`

Regras:
- Mês com dois dígitos e ano com quatro, separados por `_` (ex: `04_2026`).
- Nome do cliente em CAIXA quando vier como prefixo de relatório.
- Salvar sempre dentro da subpasta correta da estrutura do cliente — nunca na raiz da pasta do cliente.

## Quando criar um CLAUDE.md específico do cliente

Para cada cliente com especificidade relevante (plano de contas customizado, sistema fora do padrão, regras tributárias particulares, ciclo de fechamento diferente), criar um `CLAUDE.md` adicional dentro da pasta do cliente — ele complementa, não substitui, o método geral.
