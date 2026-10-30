# Plano de instalação e primeiro acesso ao FinOps

Data: 30/10/2026. Status: proposta de implementação. **Este documento não instala nem libera acesso.**

## Resultado esperado

Uma pessoa abre este GitHub, copia um único bloco para o agente de código, responde às perguntas iniciais, faz login e termina com o FinOps funcionando no agente. A mesma instalação pode ser iniciada por um executável baixado em Releases.

O cliente não precisa localizar uma pasta no Drive, editar arquivos de configuração, descobrir comandos, instalar Python manualmente ou copiar tokens. A documentação, o bloco de instalação, os instaladores, as versões e o diagnóstico partem deste repositório. Autenticação, dados e permissões continuam no FinOps.

O produto continua sendo o acesso amplo às ferramentas autorizadas do FinOps. O teste inicial usa leitura; isso não transforma a oferta em um produto limitado a consultas. Escritas e aprovações seguem as permissões efetivas do servidor.

## 1. Perguntas no início

O README mostra estas perguntas antes do bloco de instalação. O agente as apresenta juntas e aproveita respostas já fornecidas. Não pede que a pessoa descubra informações que ele pode detectar.

| Pergunta ao usuário | Respostas e comportamento |
| --- | --- |
| Você já tem acesso ao FinOps? | Sim / recebi um convite / ainda não. Sem acesso, conduzir cadastro ou resgate do convite; informar uma pendência de liberação quando existir. |
| Qual e-mail você usa ou vai usar no FinOps? | Confirmar a conta. O login autenticado deve corresponder ao e-mail informado; divergência pede escolha explícita. |
| Como você entra no FinOps? | Google / e-mail e senha / não sei. Google segue para o navegador. E-mail e senha abre a tela de login. “Não sei” abre a página de entrada e ajuda a identificar o método. |
| Você consegue concluir a verificação em duas etapas, se ela aparecer? | Sim / preciso recuperar o acesso / não sei. O sistema detecta se a conta exige a verificação e conduz o fluxo existente. |
| Vai usar para uma empresa, suas finanças pessoais ou para integrar um sistema? | Define o próximo passo e as perguntas específicas. Não concede permissões. |
| Qual empresa ou ambiente deseja conectar? | Depois do login, escolher entre os ambientes autorizados. Se não existir, conduzir a solicitação ou criação permitida. Nunca pedir UUID. |
| O que quer fazer primeiro? | Ex.: conectar bancos, consultar contas, conciliar ou conectar um sistema. Mostrar apenas os recursos disponíveis para esse acesso. |

**Onde entram usuário e senha:** o e-mail pode ser respondido ao agente. A senha é digitada pela própria pessoa em campo protegido da tela de login, somente quando esse for o método escolhido. Códigos MFA e convites secretos também são preenchidos fora do chat. Quem usa Google não precisa criar uma senha adicional. O agente recebe o resultado da autenticação, não os segredos.

Sistema operacional, arquitetura, agente em execução, versão e instalação existente são detectados. Só perguntar se a detecção falhar. Se o agente estiver em uma máquina remota, confirmar onde a instalação deve ocorrer; não confundir essa máquina com o computador da pessoa.

Para integração de sistema, perguntar também o nome do sistema, onde ele roda, qual repositório deve receber a integração e quais operações precisa consumir. Não solicitar credenciais do servidor nessa conversa inicial.

## 2. Uma entrada no GitHub

Repositório: [pedromagnago/fullbpo-claude](https://github.com/pedromagnago/fullbpo-claude).

O início do README, depois da implementação, terá esta ordem:

1. “Conecte seu agente ao FinOps”.
2. Requisitos em uma frase: agente compatível instalado e acesso ou convite do FinOps; o fluxo explica como obter o acesso quando ele falta.
3. Perguntas iniciais acima, com a observação de onde preencher a senha.
4. **Copiar para o agente:** um bloco de texto com o botão nativo de cópia do GitHub.
5. **Baixar instalador:** links para os arquivos da mesma versão estável em Releases.
6. O que deve aparecer ao terminar e um link para resolver problemas.

O cliente recebe esse único endereço. Sem PDF obrigatório, ZIP personalizado por cliente, conta GitHub, PAT ou Drive compartilhado para instalar. A identidade e os ambientes vêm do FinOps depois do login.

### Bloco proposto para copiar

Este é o texto planejado para a entrega. **Enquanto existir apenas este plano, ele deve informar que a instalação nova ainda não está publicada.** Não é um comando de instalação já implementado.

```text
Quero conectar meu agente ao FinOps da FullBPO.

Acesse https://github.com/pedromagnago/fullbpo-claude e siga a
instalação oficial indicada no README. Comece pelas perguntas de
acesso, e-mail, forma de login, ambiente e objetivo. Detecte meu
computador e o agente; pergunte só o que não conseguir identificar.

Use o instalador da versão estável publicada nesse repositório.
Abra a tela de autenticação para eu entrar com Google ou e-mail
e senha e concluir a verificação em duas etapas, quando exigida.
Não peça senha, código de verificação ou token nesta conversa.

Configure o MCP, confirme minha identidade e o ambiente autorizado
e faça uma consulta de leitura para testar. Ao terminar, diga o
que foi instalado, qual ambiente está conectado e como começar.
Se faltar cadastro ou liberação, conduza essa etapa e mostre a
pendência exata. Não declare a conexão concluída antes do teste.

Se a instalação ainda estiver apenas planejada, ou meu agente
não for compatível, informe isso. Não improvise outro instalador,
não procure credenciais em pastas e não altere meu projeto.
```

O bloco chama um procedimento determinístico e versionado. O agente não deve escrever um instalador novo para cada cliente. O README e o guia do agente devem conter exatamente o mesmo bloco, validado na publicação.

## 3. Experiência do instalador

**Perguntas → preparar computador → entrar no FinOps → confirmar ambiente → conectar MCP → testar → primeiro uso.**

- Preparar os componentes faltantes sem duplicar instalações nem apagar configurações do agente. Preservar outros MCPs e arquivos do projeto.
- Baixar configuração pública e pacote de uma release oficial. Retirar a dependência obrigatória do Drive e do mapa local de empresas.
- Usar o navegador para Google ou e-mail/senha, com MFA. Não orientar desativar MFA ou criar senha para uma conta Google.
- Confirmar o usuário autenticado e consultar seus ambientes no servidor. Se houver vários, pedir a escolha com nomes legíveis.
- Instalar o MCP no agente escolhido, no escopo apropriado, e orientar uma única reabertura da sessão se necessária. Não alterar permissões globais para ignorar confirmações.
- Executar uma consulta de leitura no ambiente escolhido. “Nenhum lançamento cadastrado” é diferente de “sem permissão” ou “falha de conexão”.
- Mostrar o primeiro pedido sugerido conforme o objetivo. Para Open Finance, abrir o fluxo autenticado de conexão bancária; consentimento bancário continua sendo feito pela pessoa.
- Se interrompido, retomar da última etapa válida. Se executado novamente, reparar ou atualizar, sem criar outro usuário, empresa ou registro de MCP.

Estados visíveis: “Preparando”, “Aguardando seu login”, “Aguardando liberação”, “Conectado” e “Precisa de ajuste”. Cada erro informa o que aconteceu e a próxima ação. O diagnóstico deve distinguir versão incompatível, rede, login, MFA, autorização, cadastro ausente e indisponibilidade do FinOps.

Não instalar Gmail, ClickUp, D4Sign ou outros conectores como pré-requisito para conectar ao FinOps. Integrações adicionais aparecem depois, quando o objetivo escolhido exigir.

## 4. O que existe e o que precisa mudar

Base conferida no GitHub em 30/10/2026: commit `20d4676a1bed11653012f04a66e5153c9458e8e7`, plugin `1.4.1`.

| Componente atual | Alteração planejada |
| --- | --- |
| README com instalação voltada ao time interno | Entrada única para cliente e operador, com perguntas e bloco copiável. |
| `plugins/fullbpo/commands/full-setup.md` | Conduzir o fluxo novo; deixar os demais conectores como opcionais. |
| `plugins/fullbpo/mcp/config.py` | Configuração pública distribuída pelo pacote; Drive passa a ser compatibilidade legada. |
| `plugins/fullbpo/mcp/finops_client.py` | Sessão obtida pelo login no navegador, renovação e reconexão; sem exigir senha salva para contas Google. |
| `plugins/fullbpo/.mcp.json` | Registrar o componente compatível com cada sistema, preservando as instalações existentes. |
| `plugins/fullbpo/mcp/finops_tools.py` e ponte existente | Reutilizar execução, recibos e catálogo; o servidor continua decidindo acesso e aprovação. |
| `tests/test_finops.py` | Complementar com testes do login, configuração, instalação repetida, falhas e isolamento. |

A API atual recebe `{tool, params}`. Essa porta HTTP não deve ser apresentada como um servidor MCP remoto pronto para adicionar por URL. Para a primeira versão, reaproveitar a ponte MCP local e acrescentar o login pelo navegador. Um servidor MCP remoto com OAuth é uma evolução possível, não requisito para começar.

### Autenticação e liberação no FinOps

Estas mudanças pertencem ao backend e às telas do FinOps, no repositório próprio. O cliente continua recebendo apenas este GitHub como entrada para instalação.

- Implementar autorização da instalação usando o login existente, incluindo Google e MFA. Entregar uma sessão vinculada à instalação por código temporário, de uso único, com proteção contra troca de sessão. Validar o desenho do retorno ao aplicativo antes de empacotar.
- Guardar a sessão no armazenamento protegido do sistema operacional; não salvar senha em texto, token em URL, argumento de processo, GitHub, log ou resposta ao agente. No Windows, usar proteção do Windows; `chmod 600` sozinho não resolve esse ambiente.
- Confirmar perfil, empresa e ferramentas no servidor. O cliente não escolhe ser administrador. O código FinOps consultado tem barreira de staff; validar o estado publicado e implementar o acesso externo antes do piloto externo, sem promover clientes a funcionários para contornar essa barreira.
- Disponibilizar cadastro/convite para quem ainda não tem acesso. A criação deve evitar duplicatas e atribuir apenas as permissões autorizadas. Se depender de liberação interna, mostrar essa dependência de forma rastreável.
- Para PF, validar o suporte do modelo de dados antes da ativação. Não inventar CNPJ nem misturar o cadastro pessoal com uma empresa.
- Permitir desconectar uma instalação e revogar seu acesso; testar o prazo efetivo de revogação, inclusive com token ainda válido.

### API para o sistema do cliente

O mesmo GitHub terá documentação, exemplos e configuração de integração. Um instalador de MCP não implementa automaticamente a integração no ERP ou no OS do cliente.

Depois do login do responsável, o fluxo de integração deve permitir solicitar/emitir uma identidade própria para o sistema, limitada aos ambientes e operações autorizados. O segredo fica no backend do sistema consumidor. Não reutilizar permanentemente a sessão pessoal do operador ou fornecer `service_role`.

A instrução ao agente abre o projeto escolhido, apresenta as alterações necessárias e valida uma primeira consulta. Escritas, sincronização, paginação e tratamento de repetição precisam de contratos próprios. Um exemplo de leitura não comprova sincronização completa.

## 5. Organização proposta do repositório

```text
README.md                           # entrada: perguntas, copiar, baixar, testar
docs/instalacao/AGENTE.md             # procedimento seguido pelo agente
docs/instalacao/primeiro-acesso.md    # login, cadastro, convite, escolha de ambiente
docs/instalacao/problemas.md          # mensagens reais e como continuar
docs/api/README.md                   # integração de sistemas
install/bootstrap.ps1               # início pelo agente no Windows
install/bootstrap.sh                # início pelo agente no macOS
installer/                          # mesmo motor usado pelo agente e executável
releases/stable.json                # versão estável, compatibilidade e URLs oficiais
plugins/fullbpo/                     # plugin existente, evoluído
tests/installer/                    # instalação, recuperação e autenticação
.github/workflows/release.yml        # construir, conferir e publicar release
```

Os caminhos acima são planejados. Só passam a aparecer como instrução utilizável no README após publicação e teste dos respectivos arquivos.

Releases conterá o `.exe` do Windows e o pacote correspondente do macOS, com versões e hashes verificáveis. Validar a assinatura dos pacotes e o comportamento real dos avisos do Windows/macOS; não orientar a desativar proteções do sistema. As arquiteturas suportadas devem estar explícitas. Não anunciar compatibilidade sem teste.

O bootstrap consulta a versão estável, fixa aquela versão durante toda a instalação e verifica o artefato antes de executá-lo. A publicação usa revisão, builds rastreáveis e manifesto atualizado só depois dos testes. Hash isolado não substitui a confiança no publicador.

O GitHub público contém código, configuração pública e exemplos fictícios. Contas, carteiras, convites secretos, dados financeiros e evidências reais de clientes ficam fora dele. Não exigir acesso ao repositório privado do FinOps para instalar.

## 6. Ordem de execução

| Etapa | Trabalho | Condição para avançar |
| --- | --- | --- |
| 1. Primeiro acesso | Validar identidade cliente, cadastro PJ/PF, login Google/senha com MFA, autorização da instalação e revogação no FinOps. | Uma conta de teste externa entra e consulta apenas seu ambiente. |
| 2. Instalador comum | Retirar Drive obrigatório, preparar componentes, armazenar sessão, detectar agente e instalar/reparar MCP. Prioridade: Windows + Claude Code. | Instalação limpa e repetida funcionam sem intervenção técnica. |
| 3. Copiar para o agente | Publicar guia e bootstrap da mesma versão; adaptar `/full-setup`; testar o bloco do README integralmente. | Pessoa parte apenas do GitHub e chega à consulta autenticada. |
| 4. Executáveis e atualização | Empacotar Windows e macOS, publicar release, verificar atualização e restauração da configuração anterior. | Pacotes reais passam nos sistemas anunciados. |
| 5. Integração de sistemas | Identidade própria de integração, documentação de API e exemplo no backend consumidor. | Consulta pelo sistema funciona sem sessão de chat aberta. |
| 6. Piloto e entrega | Testar com usuário novo; completar primeiro uso escolhido; registrar onde a pessoa precisou de ajuda. | Critérios abaixo atendidos, release estável apontada no README. |

Outros agentes de código recebem adaptadores depois de testar o caminho principal. O bloco não deve afirmar suporte universal; identifica o agente e informa quando ainda não há adaptação disponível.

## 7. Critérios de aceite

- Um usuário novo começa somente pelo GitHub e chega a uma consulta do seu ambiente, sem pedir pasta, chave ou comando ao responsável técnico.
- Login Google funciona sem criar senha. E-mail/senha funciona pela tela de login. MFA é concluído e permanece habilitado.
- Sem conta, convite inválido, ambiente ausente e acesso pendente têm caminhos explícitos. Não há falso “concluído”.
- Windows + Claude Code é testado em ambiente limpo, inclusive caminho com espaços/acentos e falta de dependências. macOS passa pelo mesmo percurso antes de ser anunciado.
- Executável e bloco copiável usam a mesma versão e produzem o mesmo resultado.
- Reexecutar, interromper, reconectar, trocar de usuário, atualizar e desinstalar preservam os outros MCPs e os dados do usuário. Nenhuma exclusão de dados financeiros faz parte da desinstalação.
- Conta de um ambiente não lê nem escreve em outro; catálogo respeita o perfil. Escolher um nome no instalador não amplia acesso.
- Não há senha, token ou segredo de convite no chat, logs, linha de comando, Git ou diagnóstico. Relatório compartilhável contém somente versão, etapa, código do erro e identificador de suporte não secreto.
- Revogação, sessão expirada, falta de rede e indisponibilidade do serviço não provocam repetição automática de uma escrita com resultado desconhecido.
- “Conectado ao FinOps” exige consulta autenticada. “Banco conectado” exige o fluxo bancário concluído e a primeira leitura validada; são resultados distintos.
- Para API, testar o consumidor com identidade própria e sem Claude aberto. PF e PJ permanecem separados.

Meta de usabilidade: a pessoa não precisar de explicação por áudio ou intervenção para editar arquivos. Medir tempo e pontos de ajuda no piloto antes de prometer prazo de instalação.

## 8. Entrega desta proposta e referências

Esta alteração publica somente o plano e seu acesso pelo README. Não altera plugin, versão, servidor, cadastro, credenciais ou permissões. O bloco acima é uma especificação; os instaladores ainda precisam ser construídos e validados.

Referências conferidas em 30/10/2026:

- [README da base analisada](https://github.com/pedromagnago/fullbpo-claude/blob/20d4676a1bed11653012f04a66e5153c9458e8e7/README.md).
- [Configuração da versão analisada](https://github.com/pedromagnago/fullbpo-claude/blob/20d4676a1bed11653012f04a66e5153c9458e8e7/plugins/fullbpo/mcp/config.py) e [autenticação atual](https://github.com/pedromagnago/fullbpo-claude/blob/20d4676a1bed11653012f04a66e5153c9458e8e7/plugins/fullbpo/mcp/finops_client.py).
- [Instalação e gestão de plugins no Claude Code](https://code.claude.com/docs/en/discover-plugins).
- [MCP e autenticação no Claude Code](https://code.claude.com/docs/en/mcp).
