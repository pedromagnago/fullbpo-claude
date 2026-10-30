# FullBPO — Plugin Claude Code

Pacote oficial de agentes, comandos e skills da **FullBPO** para Claude Code. Institucionaliza o método da operação: todo mundo do time usa as mesmas ferramentas, na mesma versão, atualizadas de um lugar só.

## O que vem dentro

- **58 agentes especialistas** (pt-BR) — fiscal (Simples, ICMS/ISS, PIS/COFINS, IRPJ/CSLL, IPI, SPED, ECF/ECD, DCTFWeb, Reinf), folha/DP (eSocial, holerite, férias/13º, rescisão, INSS/FGTS, admissão), conciliações (banco, cartão, fornecedores, clientes), fechamento mensal, DRE gerencial, fluxo de caixa, controladoria, societário (abertura, alteração, baixa), malha fina, due diligence, valuation e mais. Orquestrador: `controladoria-fullbpo`.
- **9 comandos de rotina** — `/fechamento`, `/conciliar`, `/relatorio-cliente`, `/onboarding`, `/apurar`, `/cobrar-docs`, `/prazos`, `/mentoria`, `/full-setup`.
- **3 skills de método** — `metodo-fullbpo`, `voz-da-marca`, `nomenclatura-full`.
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

Na versão **1.5.0**, o MCP `fullbpo-omie` também opera o FinOps:

- Os 58 agentes herdam as ferramentas disponíveis na sessão e carregam a orientação `operar-finops`, respeitando as permissões do login.
- `finops_contexto`: login, escopo, versões e limitações.
- `finops_mapa`: caminhos de tela, cobertura do MCP e orientação por objetivo.
- `finops_implantacao`: checklist operacional da carteira, com prévia, versão, alerta de duplicidade e leitura posterior.
- `finops_empresas`: carteira atual do login, consultada no servidor.
- `finops_ferramentas` e `finops_executar`: catálogo completo e execução com permissões individuais.
- `finops_tarefas`: consulta, criação, atualização e checklist no quadro, sem acionar outra IA.
- `finops_onboarding`: consulta administrativa de propostas, contratos e etapas; aproveita a D4Sign configurada no FinOps.
- `finops_decidir_pendencia`: leva ao servidor a decisão explícita da pessoa sobre uma pendência.

O Claude faz a análise na conta de quem está trabalhando. O FinOps guarda os registros, aplica as permissões e mantém a auditoria. A versão requer as ferramentas `listar_empresas`, `manage_tarefas`, `comercial_onboarding`, `finops_contexto`, `finops_mapa` e `manage_implantacao` publicadas no backend. O arquivo `finops_empresas.json` antigo deixa de ser a fonte da carteira.

Quando sair uma versão nova, execute no terminal:
```sh
claude plugin marketplace update fullbpo
claude plugin update fullbpo@fullbpo
```

Na interface do Claude Code, a alternativa é abrir `/plugin`, entrar em **Installed**, selecionar **FullBPO** e escolher **Update now**. Reinicie a sessão do Claude e rode `/full-setup`. Valide primeiro leitura e prévia. Para escrita, use uma tarefa de teste identificada, não um lançamento financeiro ou envio ao cliente.

## Manutenção (Pedro / responsável)

O conteúdo vive neste repositório:
```
fullbpo-claude/
├── .claude-plugin/marketplace.json     → declara o marketplace
└── plugins/fullbpo/
    ├── .claude-plugin/plugin.json       → metadata e versão do plugin
    ├── agents/                          → 58 agentes (.md)
    ├── commands/                        → comandos de rotina (.md)
    ├── skills/                          → skills de método
    └── CLAUDE.md                        → contexto modelo
```

Para publicar uma melhoria:
1. Edite o agente/comando/skill.
2. Suba a `version` em `plugins/fullbpo/.claude-plugin/plugin.json`.
3. `git commit` + `git push`.
4. O time atualiza o plugin pelo terminal ou pelo painel, conforme as instruções acima.

Atalho: editou um agente direto em `~/.claude/agents/`? Copie de volta para `plugins/fullbpo/agents/` antes do commit, para manter o repositório como fonte da verdade.
