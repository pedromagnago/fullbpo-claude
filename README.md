# FullBPO — Plugin Claude Code

Pacote oficial de agentes, comandos e skills da **FullBPO** para Claude Code. Institucionaliza o método da operação: todo mundo do time usa as mesmas ferramentas, na mesma versão, atualizadas de um lugar só.

## O que vem dentro

- **58 agentes especialistas** (pt-BR) — fiscal (Simples, ICMS/ISS, PIS/COFINS, IRPJ/CSLL, IPI, SPED, ECF/ECD, DCTFWeb, Reinf), folha/DP (eSocial, holerite, férias/13º, rescisão, INSS/FGTS, admissão), conciliações (banco, cartão, fornecedores, clientes), fechamento mensal, DRE gerencial, fluxo de caixa, controladoria, societário (abertura, alteração, baixa), malha fina, due diligence, valuation e mais. Orquestrador: `controladoria-fullbpo`.
- **9 comandos de rotina** — `/fechamento`, `/conciliar`, `/relatorio-cliente`, `/onboarding`, `/apurar`, `/cobrar-docs`, `/prazos`, `/mentoria`, `/full-setup`.
- **3 skills de método** — `metodo-fullbpo`, `voz-da-marca`, `nomenclatura-full`.
- **2 servidores MCP embutidos** — `fullbpo-omie` (Omie via FinOps: consulta e lançamento de contas a pagar/receber, baixas e cadastros — escrita sempre em `dry_run` por padrão, com confirmação humana) e `fullbpo-d4sign` (contratos D4Sign: listar/baixar documentos, criar, definir signatários e enviar para assinatura — envio atrás de `dry_run`). Credenciais locais em `~/.fullbpo/credenciais.env` (modelo em `plugins/fullbpo/mcp/credenciais.env.example`).
- **CLAUDE.md modelo** — contexto operacional para copiar na pasta de trabalho.

## Instalação (time)

Pré-requisitos: Claude Code instalado, licença ativa e conta Claude com os conectores conectados (ver passo 3).

1. **Adicionar o marketplace da FullBPO:**
   ```
   /plugin marketplace add pedromagnago/fullbpo-claude
   ```
2. **Instalar o plugin:**
   ```
   /plugin install fullbpo@fullbpo
   ```
3. **Rodar o setup guiado** (conecta MCPs, permissões e contexto):
   ```
   /full-setup
   ```
4. **(Opcional, recomendado) contexto sempre-ligado:** copie `plugins/fullbpo/CLAUDE.md` para a raiz da sua pasta de trabalho no Drive.

Pronto. Teste com `/prazos 06/2026`.

> Os conectores (Google Drive, Gmail, Calendar, ClickUp, etc.) **não vêm no plugin** — cada pessoa conecta na própria conta Claude corporativa @fullbpo.com. O plugin distribui o know-how; o acesso e a licença são de cada um.

## Atualização

Quando sair uma versão nova:
```
/plugin marketplace update fullbpo
/plugin update fullbpo@fullbpo
```

## Manutenção (Pedro / responsável)

O conteúdo vive neste repositório:
```
fullbpo-claude/
├── .claude-plugin/marketplace.json     → declara o marketplace
└── plugins/fullbpo/
    ├── .claude-plugin/plugin.json       → metadata e versão do plugin
    ├── .mcp.json                        → declara os servidores MCP do plugin
    ├── agents/                          → 58 agentes (.md)
    ├── commands/                        → comandos de rotina (.md)
    ├── skills/                          → skills de método
    ├── mcp/                             → servidores MCP (Omie/FinOps, D4Sign)
    └── CLAUDE.md                        → contexto modelo
```

Para publicar uma melhoria:
1. Edite o agente/comando/skill.
2. Suba a `version` em `plugins/fullbpo/.claude-plugin/plugin.json`.
3. `git commit` + `git push`.
4. O time roda `/plugin update` e recebe a mudança.

Atalho: editou um agente direto em `~/.claude/agents/`? Copie de volta para `plugins/fullbpo/agents/` antes do commit, para manter o repositório como fonte da verdade.
