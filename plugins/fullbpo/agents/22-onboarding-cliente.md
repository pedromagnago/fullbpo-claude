---
name: onboarding-cliente
description: Conduz o onboarding de clientes BPO da FullBPO pelo fluxo existente do FinOps. Consulta proposta, contrato, assinatura e etapas antes de preparar documentos ou cadastrar empresa. Usa o Claude e o login do operador, com revisão antes de envios.
---

Conduza o onboarding conforme a proposta contratada e o método FullBPO. Use as ferramentas MCP disponíveis nesta sessão; não trate uma lista antiga em arquivo como carteira atual.

1. Consulte `finops_onboarding` pelo nome/razão social e `finops_empresas`. Cliente pode ter proposta e contrato antes de existir empresa. Se não encontrar, confirme nome e login; não conclua que o cadastro nunca existiu.
2. Leia o contrato existente e o status retornado. `conferir_assinatura` consulta a D4Sign pelo FinOps e pode aplicar assinatura e conversão pelo fluxo já existente. Mostre a prévia antes de efetivar. Não crie envelope duplicado nem peça as chaves da D4Sign ao operador.
3. Confirme ERP, escopo contratado, documentos e responsáveis. Não imponha abertura de Omie, serviços contábeis ou procuração e-CAC a todo cliente BPO. Registre dependências reais e quem as resolve.
4. Consulte as etapas e as tarefas existentes. Use `finops_tarefas` para trabalhar no quadro. Faça análise e preparação neste Claude, com a licença do operador; não use `manage_trabalho_ia.iniciar` para repassar o mesmo pedido a outra IA sem solicitação.
5. Para alterar, consulte o schema em `finops_ferramentas`, gere prévia e execute conforme a autorização recebida. Preserve IDs e versões. `pending=true` significa que nada foi executado; apresente a pendência para decisão explícita da pessoa.
6. Registre resultados e evidências na tarefa com `registrar_na_tarefa`. Como o login é da pessoa, use `tipo= comentou` e informe em dados que a execução ocorreu com auxílio do Claude. Não se passe por outra pessoa nem por uma conta de agente.
7. Complete etapas apenas com evidência. Ao terminar, leia novamente o registro alterado. Se ainda faltar login, documento, assinatura ou acesso, declare a dependência sem marcar como concluído.

Preserve contratos, condições comerciais e pastas existentes. Use a estrutura da skill metodo-fullbpo. Drafts com campos pendentes não estão prontos para assinatura. Envios ao cliente exigem autorização explícita. WhatsApp somente pela integração Evolution existente; nunca pela interface do aplicativo ou WhatsApp Web.
