# API FinOps para o sistema do cliente

A mesma autorização do FinOps Connect pode gerar uma credencial para seu servidor. Escolha **Integrar meu sistema pela API** no assistente. Após autorizar no FinOps, clique em **Exportar credencial para meu servidor**. O arquivo contém `endpoint`, `token` e `company_id`.

Guarde o token no cofre de segredos do servidor. Não coloque no frontend, GitHub, logs ou mensagens. A exportação não é necessária para usar o Claude Code.

Endpoint: `POST https://rlznohwlgcfjbbgnwozf.supabase.co/functions/v1/agent-connect`

Headers: `Content-Type: application/json` e `Authorization: Bearer <token>`. Esta API usa a credencial `fna_…` emitida pelo instalador; não usa senha, JWT pessoal, chave de administrador ou service_role.

## Consultas

| `tool` | Parâmetros | Resultado |
|---|---|---|
| `finops_empresa` | `{}` | Empresa, escopo e validade |
| `finops_contas` | `limit`, `offset` | Contas e saldo registrado no FinOps |
| `finops_movimentos` | `data_de`, `data_ate`, `conciliado`, `limit`, `offset` | Movimentos por data, conta e conciliação |
| `finops_titulos` | `tipo`: `pagar` ou `receber`; opcionais `data_de`, `data_ate`, `status`, `limit`, `offset` | Títulos por vencimento, com previsão e valor liquidado |

```json
{"action":"call","tool":"finops_titulos","params":{"tipo":"pagar","limit":50,"offset":0}}
```

A empresa é definida pela credencial. Se enviar `company_id`, ele precisa ser o da autorização; outra empresa é recusada. Não existe parâmetro para consultar todas as empresas.

Listas retornam `data.records`, `data.has_more` e `data.next_offset`. Limite padrão 50, máximo 200. Siga `next_offset` até `has_more=false`; a primeira página não representa um total financeiro. Paginação por offset pode mudar se os dados forem alterados durante a consulta; deduplique por `id`.

As datas são `YYYY-MM-DD`. Nos títulos, os filtros se referem ao **vencimento**. Use os campos de previsão para análise de caixa. `valor` é o valor original; considere `valor_pago` ou `valor_recebido` para o saldo em aberto. Saldos dependem da atualização dos dados no FinOps, sem garantia de atualização bancária instantânea.

## Exemplo Node.js

O exemplo usa `FINOPS_TOKEN` vindo do cofre do seu servidor. Não imprima essa variável.

```js
const response = await fetch(
  'https://rlznohwlgcfjbbgnwozf.supabase.co/functions/v1/agent-connect',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${process.env.FINOPS_TOKEN}`,
    },
    body: JSON.stringify({
      action: 'call', tool: 'finops_contas', params: { limit: 50, offset: 0 },
    }),
  },
);
if (!response.ok) throw new Error(`FinOps: HTTP ${response.status}`);
const result = await response.json();
// Trate result.data no seu sistema; não registre dados financeiros sem necessidade.
```

## Validade e erros

Credencial de 90 dias, revogável no FinOps. A permissão da pessoa e a situação da empresa são conferidas em cada chamada. Não há renovação silenciosa pelo cliente.

- `401`: credencial inválida, revogada ou expirada; autorize novamente.
- `403`: empresa sem acesso ou ferramenta fora do escopo.
- `400`: parâmetros inválidos.
- `429`: limite de 120 chamadas por minuto; aguarde antes de tentar novamente.
- `500`: consulta não confirmada; não presuma resultado vazio.

A resposta de erro usa `{"error":"codigo"}`. Todas as consultas deste piloto são de leitura. O MCP interno `/mcp-server` continua separado e não é o endpoint para estes tokens.
