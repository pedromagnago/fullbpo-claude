---
description: Conciliação FullBPO — banco, cartão/credenciadora, fornecedores ou clientes
argument-hint: [tipo: banco|cartao|fornecedores|clientes] [cliente] [mês/ano]
---
Faça a conciliação do tipo **$1** para o cliente **$2** em **$3**.

Roteie para o agente correto:
- `banco` → `16-conciliacao-bancaria`
- `cartao` → `38-conciliacao-cartoes-credenciadora`
- `fornecedores` → `39-conciliacao-fornecedores`
- `clientes` → `40-conciliacao-clientes`

Feche com tolerância zero, liste as pendências a regularizar e os lançamentos a fazer (D/C). pt-BR, padrão FullBPO. Indique onde salvar no Drive do cliente, seguindo a nomenclatura `Conciliacao_[Tipo]_[MM_AAAA].xlsx`.
