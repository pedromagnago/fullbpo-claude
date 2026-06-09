---
description: Apuração tributária mensal — roteia para o regime certo (Simples, MEI, ICMS/ISS, PIS/COFINS, IRPJ/CSLL, IPI)
argument-hint: [cliente] [tributo ou regime] [mês/ano]
---
Apure os tributos do cliente **$1** ($2) referente a **$3**.

Roteie para o agente correto conforme o regime/tributo:
- Simples Nacional → `01-apuracao-simples-nacional`
- MEI → `28-apuracao-mei`
- ICMS / ISS → `02-icms-iss`
- PIS / COFINS → `03-pis-cofins`
- IRPJ / CSLL → `04-irpj-csll`
- IPI → `29-calculo-ipi`

Mostre o cálculo passo a passo, gere a guia (DAS/DARF/GNRE) com vencimento e rode o `05-conferencia-guia` antes de entregar. pt-BR. Sinalize qualquer estimativa como tal — nunca invente dado fiscal; se faltar informação, peça.
