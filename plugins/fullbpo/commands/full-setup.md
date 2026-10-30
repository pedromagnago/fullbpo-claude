---
description: Guia de configuração inicial do Claude para um novo membro do time FullBPO (MCPs, permissões, contexto)
---
Você está configurando o Claude para um novo membro do time FullBPO. Conduza o setup em passos claros, em pt-BR, sem jargão:

Primeiro chame `finops_contexto` e confira a identidade e as versões. O plugin 1.5.0 inclui `finops_mapa` e `finops_implantacao`. Consulte o mapa para explicar telas e limites. Depois valide o FinOps: `finops_empresas` deve consultar a carteira do servidor; `finops_ferramentas` deve mostrar `manage_tarefas` e `comercial_onboarding`. O MCP `fullbpo-omie` usa o login individual do FinOps guardado localmente em `~/.fullbpo/credenciais.env`. Não peça senha no chat nem copie o login de Pedro. Se a identidade estiver errada, a pessoa deve corrigir o arquivo local em seu computador. Nunca imprima senha, access token ou refresh token.

Se essas ferramentas não aparecerem, atualize o marketplace e o plugin FullBPO e reinicie a sessão. Não edite a cópia em cache. A D4Sign local é um conector separado: para contratos do FinOps, use `finops_onboarding`, que aproveita a conexão do servidor.

Para validar escrita, apresente uma tarefa de teste à pessoa, crie com UUID estável e leia de volta. Não use lançamentos financeiros nem envio ao cliente como teste. Registre qual etapa foi verificada: configuração, leitura, prévia ou escrita persistida.

1. **Conectores (MCP):** oriente a conectar na conta Claude os conectores que a operação usa — Google Drive, Gmail, Google Calendar e ClickUp (e, se for da área técnica, n8n, Supabase, Vercel). Cada pessoa conecta com a própria conta corporativa @fullbpo.com. Esses conectores NÃO vêm dentro do plugin: são da conta de cada um.

2. **Permissões:** mostre o bloco de `permissions.allow` recomendado para o `settings.json` (leitura de Drive/Gmail/Calendar/ClickUp), pra reduzir os pop-ups de autorização, e explique como aplicar.

3. **Contexto operacional:** confirme que o método FullBPO está disponível — a skill `metodo-fullbpo` cobre estrutura de pastas, plano de contas, sistemas dos clientes e voz da marca; as skills `voz-da-marca` e `nomenclatura-full` complementam. Para contexto sempre-ligado, oriente a copiar o `CLAUDE.md` modelo (incluído no repositório) para a raiz da pasta de trabalho no Drive.

4. **Validação:** peça para testar com `/prazos 06/2026` ou invocar o agente `controladoria-fullbpo`, e confirme que respondeu no padrão FullBPO (pt-BR, tom da marca).

Ao final, gere um checklist do que ficou configurado e o que ainda falta.
