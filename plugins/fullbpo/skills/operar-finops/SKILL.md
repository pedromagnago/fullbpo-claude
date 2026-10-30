---
name: operar-finops
description: Trabalhar no FinOps com o Claude do operador: consultar e alterar tarefas, onboarding, CRM, dados financeiros e conciliação pelo MCP. Use quando a pessoa pedir uma ação no FinOps, inclusive ao continuar um onboarding ou fechamento.
---

Use o MCP `fullbpo-omie` já instalado, com o login da pessoa. Não copie credenciais de Pedro nem peça segredo no chat.

0. Comece por `finops_contexto` para conferir login, versões e escopo. Quando a pessoa perguntar onde acompanhar ou como fazer, consulte `finops_mapa` pelo objetivo. Não procure a interface na pasta do cliente nem deduza menus pelos nomes das tabelas. O mapa informa cobertura e limites; disponibilidade no catálogo não concede acesso nem comprova que uma integração funciona.
1. Consulte `finops_empresas` para a carteira atual. Um arquivo local antigo não confirma ausência de empresa. Para cliente ainda no comercial, consulte `finops_onboarding` pelo nome/razão social.
2. Descubra ferramentas e parâmetros em `finops_ferramentas`. Não declare que algo está fora do MCP antes dessa consulta. Erro de permissão não é falta de ferramenta.
3. Leia a tarefa existente em `finops_tarefas`; faça o trabalho neste Claude. Escreva pelos endpoints do FinOps, sem SQL direto, outra IA ou serviço paralelo. Só use `manage_trabalho_ia.iniciar` se o operador pedir o motor do servidor.
4. Alterações com `dry_run` começam como prévia. Se a pessoa já autorizou a alteração concreta, execute-a; não peça a mesma confirmação novamente. Para criação de tarefa, reutilize o UUID devolvido na prévia; para atualização, use `updated_at` como `versao`.
5. Se o servidor devolver `pending=true`, nada foi executado. Mostre os detalhes, preserve o token e só decida a pendência depois da autorização explícita da pessoa para aquela ação. Nunca autoaprove. Identidades de agente continuam sem poder de decisão.
6. Registre resultado e evidência com `registrar_na_tarefa`, `tipo= comentou` para login humano e `dados.executor=claude_do_operador`. Leia o registro de volta antes de declarar conclusão. Não marque itens pendentes ou trabalho de terceiros como feito.

Contratos do FinOps usam a conexão D4Sign do servidor por `finops_onboarding`. Ausência de credencial no conector D4Sign local não significa que a integração do FinOps esteja indisponível. Confira proposta/contrato existente antes de criar outro envelope. Não presuma ERP nem escopo contábil.

O canal WhatsApp é exclusivamente a Evolution API existente na VPS. Envios e publicação exigem autorização explícita; não use a interface do WhatsApp. Falhas com resultado desconhecido exigem consulta antes de repetir escrita.

Para checklist de implantação, use `finops_implantacao` com a empresa da carteira. Propostas, contratos e assinatura continuam em `finops_onboarding`, administrativo. Duplicidade é inconsistência: preserve os registros, explique os status divergentes e não escolha uma cópia automaticamente.

Ao responder, diga o que foi consultado ou alterado, onde acompanhar e o próximo passo necessário. Preserve fonte e horário. `previa`, `aguardando_aprovacao`, `retorno_recebido` e `resultado_desconhecido` não significam conclusão. Só declare alteração confirmada com evidência e leitura posterior; nunca repita escrita com resultado incerto. Um erro 403 significa acesso negado, não ferramenta inexistente. Nunca use SQL ou credenciais de outra pessoa para contornar.
