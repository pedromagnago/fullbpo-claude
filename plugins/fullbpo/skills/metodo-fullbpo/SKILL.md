---
name: metodo-fullbpo
description: Método operacional da FullBPO (BPO financeiro brasileiro). Use sempre que trabalhar em tarefa de cliente FullBPO — estrutura de pastas por cliente, plano de contas brasileiro, sistemas de origem dos dados (Conta Azul, Omie, Sankhya, Domínio, Bling), convenções pt-BR e regras de segurança operacional.
---

# Método Operacional FullBPO

A FullBPO é um BPO Financeiro brasileiro que entrega backoffice contábil-financeiro completo para PMEs. Cada subpasta numerada em `02 - Operação/` é um cliente ativo. A entrega não é só execução — é **clareza, previsibilidade e insight**.

## Idioma e formato — sempre pt-BR

- Toda análise, relatório, comentário, e-mail e deck em **português do Brasil**.
- **Datas:** DD/MM/AAAA (nunca MM/DD).
- **Decimal:** vírgula. Milhar: ponto. Ex: `R$ 1.234.567,89`.
- **Moeda padrão:** BRL (R$). Se vier USD/EUR, indicar a moeda explicitamente.
- **Períodos:** "abr/26", "1T26", "12M até abr/26".
- **Não traduzir literalmente termos US.** accrual → competência/provisão; AR/AP → contas a receber/pagar; GL → razão; P&L → DRE; month-end close → fechamento contábil mensal.

## Estrutura padrão por cliente

```
[NN - Cliente]/
├── 01 - Gestão Comercial/         → contratos com clientes, faturamento
├── 02 - Gestão de Suprimentos/    → contratos com fornecedores, compras
├── 03 - Gestão Financeira/        → AP, AR, tesouraria, fluxo de caixa
│   ├── 01 - Contas à Pagar/
│   ├── 02 - Contas à Receber/
│   ├── 03 - Tesouraria/
│   ├── 04 - Fluxo de Caixa/
│   ├── 05 - Relatórios/
│   └── 06 - Implantação/
├── 04 - Gestão de Resultados/     → DRE, Power BI, conferências, mentoria
└── 05 - Contabilidade/            → arquivado por ano fiscal
```

Respeite essa estrutura. Não invente pastas novas dentro do cliente.

## Plano de contas — referência brasileira

Plano brasileiro (não US GAAP). Estrutura típica do DRE:

Receita Bruta → Deduções (impostos, devoluções) → Receita Líquida → CMV/CSP → Lucro Bruto → Despesas Operacionais (Pessoal, Comercial, Administrativas, Ocupação, Tecnologia) → EBITDA → Resultado Financeiro → IR/CSLL → Lucro Líquido.

O plano exato varia por cliente — antes de classificar, **leia o plano do cliente** (geralmente em `04 - Gestão de Resultados/02 - Banco de Dados/` ou `05 - Contabilidade/[ano]/`).

## Sistemas de origem (identificar pelo layout do export)

- **Conta Azul** — colunas pt-BR, datas DD/MM/AAAA, decimal vírgula
- **Omie** — `.xlsx` com cabeçalho de identificação nas primeiras linhas
- **Sankhya** — `.csv` separador `;`, encoding latin-1 ou UTF-8 (verificar)
- **Domínio Sistemas** — `.txt` posicional ou `.csv`
- **Bling** — e-commerce/varejo, exports com SKU
- **Power BI** — em `04 - Gestão de Resultados/01 - PowerBI/`

Export com encoding quebrado (acentos errados) → limpar antes de qualquer análise.

## Regras de segurança operacional

- **Nunca alterar** arquivos em `05 - Contabilidade/[ano]/` de anos fiscais fechados sem confirmação explícita.
- **Não publicar** nada (e-mail, planilha consolidada, relatório) sem revisão humana — você produz o draft, o time revisa antes de enviar.
- **CNPJ, dados bancários, certificado digital** dos clientes são confidenciais. Nunca incluir em prompts, summaries ou logs fora do escopo da pasta do cliente.
- Dúvida de classificação contábil → **pergunte** antes de classificar. Erro de classificação contamina o DRE e a mentoria seguinte.
- Nunca inventar dado financeiro — se não tiver, sinalize como estimativa ou peça.

## Voz da marca (resumo)

A FullBPO é **"backoffice inteligente"**, não terceirizada genérica. Comunicação ao cliente: direta e empática, sem jargão desnecessário, provocativa quando preciso, sempre acionável. Ver a skill `voz-da-marca` para detalhes e exemplos.
