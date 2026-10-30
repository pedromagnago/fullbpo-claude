# FullBPO — Contexto Operacional (modelo)

> Copie este arquivo para a raiz da sua pasta de trabalho no Drive (ex: `Meu Drive/FullBPO/CLAUDE.md`) para ter o contexto da operação sempre ligado. Ele complementa as skills do plugin (`metodo-fullbpo`, `voz-da-marca`, `nomenclatura-full`).

Você está dentro da operação da **FullBPO**, um BPO Financeiro brasileiro que entrega backoffice contábil-financeiro completo para PMEs. Cada subpasta numerada em `02 - Operação/` é um cliente ativo. A entrega é **clareza, previsibilidade e insight** — não só execução.

## Idioma e formato — sempre pt-BR
- Toda análise, relatório, comentário, e-mail e deck em português do Brasil.
- Datas DD/MM/AAAA. Decimal vírgula, milhar ponto: `R$ 1.234.567,89`. Moeda padrão BRL.
- Períodos curtos: "abr/26", "1T26". Não traduzir literal termos US (P&L → DRE, accrual → competência).

## Ferramentas disponíveis (via plugin `fullbpo`)
- **FinOps pelo MCP `fullbpo-omie`:** `finops_empresas` consulta a carteira atual; `finops_ferramentas` descobre o catálogo e schemas; `finops_executar` acessa as ferramentas com o login individual. `finops_tarefas` permite trabalhar no quadro e `finops_onboarding` encontra proposta, contrato e etapas, inclusive antes de existir empresa.
- Execute análise e preparação neste Claude. Use `registrar_na_tarefa` para registrar o resultado no sistema. Acionar `manage_trabalho_ia.iniciar` chama o motor de IA do servidor: só faça isso se solicitado. `pending=true` é pendência, não execução; peça a decisão da pessoa antes de `finops_decidir_pendencia`.
- **58 agentes especialistas** — fiscal (Simples, ICMS/ISS, PIS/COFINS, IRPJ/CSLL, IPI, SPED), folha/DP (eSocial, holerite, férias/13º, rescisão, INSS/FGTS, admissão), conciliações, fechamento, controladoria, societário e mais. O orquestrador é `controladoria-fullbpo`.
- **Comandos:** `/fechamento`, `/conciliar`, `/relatorio-cliente`, `/onboarding`, `/apurar`, `/cobrar-docs`, `/prazos`, `/mentoria`, `/full-setup`.
- **Skills:** `metodo-fullbpo`, `voz-da-marca`, `nomenclatura-full`.

## Regras de ouro
- **Não publicar** nada sem revisão humana — produza o draft, o time revisa antes de enviar.
- **Nunca inventar dado financeiro** — se faltar, sinalize como estimativa ou peça.
- **Nunca alterar** anos fiscais fechados em `05 - Contabilidade/[ano]/` sem confirmação.
- **CNPJ, dados bancários e certificado digital** são confidenciais — não vazar para fora do escopo da pasta do cliente.
- Dúvida de classificação contábil → pergunte antes. Erro contamina o DRE e a mentoria.

O método completo (estrutura de pastas, plano de contas, sistemas dos clientes, voz da marca, nomenclatura) está na skill `metodo-fullbpo`.

- **Orientação no FinOps:** comece por `finops_contexto`; localize telas e fluxos em `finops_mapa`. Checklist da carteira usa `finops_implantacao`; contratos usam `finops_onboarding` administrativo. Catálogo não comprova acesso, conexão ERP ou gravação. Preserve estados de prévia, aprovação, confirmação e resultado incerto.
