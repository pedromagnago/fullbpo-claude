---
description: Guia de configuração inicial do Claude para um novo membro do time FullBPO (MCPs, permissões, contexto)
---
Você está configurando o Claude para um novo membro do time FullBPO. Conduza o setup em passos claros, em pt-BR, sem jargão:

1. **Conectores (MCP):** oriente a conectar na conta Claude os conectores que a operação usa — Google Drive, Gmail, Google Calendar e ClickUp (e, se for da área técnica, n8n, Supabase, Vercel). Cada pessoa conecta com a própria conta corporativa @fullbpo.com. Esses conectores NÃO vêm dentro do plugin: são da conta de cada um.

2. **Permissões:** mostre o bloco de `permissions.allow` recomendado para o `settings.json` (leitura de Drive/Gmail/Calendar/ClickUp), pra reduzir os pop-ups de autorização, e explique como aplicar.

3. **Contexto operacional:** confirme que o método FullBPO está disponível — a skill `metodo-fullbpo` cobre estrutura de pastas, plano de contas, sistemas dos clientes e voz da marca; as skills `voz-da-marca` e `nomenclatura-full` complementam. Para contexto sempre-ligado, oriente a copiar o `CLAUDE.md` modelo (incluído no repositório) para a raiz da pasta de trabalho no Drive.

4. **Validação:** peça para testar com `/prazos 06/2026` ou invocar o agente `controladoria-fullbpo`, e confirme que respondeu no padrão FullBPO (pt-BR, tom da marca).

Ao final, gere um checklist do que ficou configurado e o que ainda falta.
