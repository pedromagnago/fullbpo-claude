---
name: operar-finops
description: Trabalhar no FinOps com o Claude do operador: consultar e alterar tarefas, onboarding, CRM, dados financeiros e conciliação pelo MCP. Use quando a pessoa pedir uma ação no FinOps, inclusive ao continuar um onboarding ou fechamento.
---

Use o MCP `fullbpo-omie` já instalado, com o login da pessoa. Não copie credenciais de Pedro nem peça segredo no chat.

1. Consulte `finops_empresas` para a carteira atual. Um arquivo local antigo não confirma ausência de empresa. Para cliente ainda no comercial, consulte `finops_onboarding` pelo nome/razão social.
2. Descubra ferramentas e parâmetros em `finops_ferramentas`. Não declare que algo está fora do MCP antes dessa consulta. Erro de permissão não é falta de ferramenta.
3. Leia a tarefa existente em `finops_tarefas`; faça o trabalho neste Claude. Escreva pelos endpoints do FinOps, sem SQL direto, outra IA ou serviço paralelo. Só use `manage_trabalho_ia.iniciar` se o operador pedir o motor do servidor.
4. Alterações com `dry_run` começam como prévia. Se a pessoa já autorizou a alteração concreta, execute-a; não peça a mesma confirmação novamente. Para criação de tarefa, reutilize o UUID devolvido na prévia; para atualização, use `updated_at` como `versao`.
5. Se o servidor devolver `pending=true`, nada foi executado. Mostre os detalhes, preserve o token e só decida a pendência depois da autorização explícita da pessoa para aquela ação. Nunca autoaprove. Identidades de agente continuam sem poder de decisão.
6. Registre resultado e evidência com `registrar_na_tarefa`, `tipo= comentou` para login humano e `dados.executor=claude_do_operador`. Leia o registro de volta antes de declarar conclusão. Não marque itens pendentes ou trabalho de terceiros como feito.

Contratos do FinOps usam a conexão D4Sign do servidor por `finops_onboarding`. Ausência de credencial no conector D4Sign local não significa que a integração do FinOps esteja indisponível. Confira proposta/contrato existente antes de criar outro envelope. Não presuma ERP nem escopo contábil.

O canal WhatsApp é exclusivamente a Evolution API existente na VPS. Envios e publicação exigem autorização explícita; não use a interface do WhatsApp. Falhas com resultado desconhecido exigem consulta antes de repetir escrita.
