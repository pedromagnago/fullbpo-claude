# Conectar o FinOps ao Claude Code ou ao seu sistema

O FinOps Connect abre a autorização no navegador, guarda a credencial no cofre do computador e configura o Claude Code. Não depende de pasta compartilhada do Drive.

Este é um **piloto de leitura**: empresa, contas bancárias, movimentos e títulos. Pagamentos, alterações, emissão fiscal e ferramentas internas da equipe não estão habilitados.

## Antes de começar

Responda estas perguntas:

1. Você vai usar o **Claude Code** ou conectar **o sistema da sua empresa pela API**?
2. Qual empresa quer consultar? Ela precisa estar vinculada à sua conta do FinOps.
3. Você já consegue entrar no [FinOps](https://os.fullbpo.com)? Use seu e-mail individual e o mesmo método de login.
4. Tem acesso ao aplicativo autenticador? O FinOps pedirá o código de seis números.
5. Seu computador é Windows ou macOS? Para usar no Claude, o Claude Code precisa estar instalado e funcionando.

**Digite senha e código do autenticador somente na página do FinOps. Não envie pelo chat, ao agente de código ou à FullBPO.** Se ainda não tem acesso, solicite o convite e o vínculo com a empresa. O instalador não cria permissões.

## Instalar

Na [release connect-v0.1.0](https://github.com/pedromagnago/fullbpo-claude/releases/tag/connect-v0.1.0), baixe o ZIP do seu computador e extraia:

- Windows: `FinOpsConnect-Windows-x64.zip`.
- Mac com chip Apple: `FinOpsConnect-macOS-arm64.zip`.
- Mac com Intel: `FinOpsConnect-macOS-x64.zip`.

Abra `FinOpsConnect`. Ele abre um assistente no navegador. Os pacotes do piloto ainda não têm assinatura de distribuição Windows/Apple; o sistema pode pedir confirmação de origem. Se a política da sua empresa bloquear o programa, peça à TI a liberação deste pacote — não desligue a proteção do computador.

1. Escolha **Usar no Claude Code** ou **Integrar meu sistema pela API**.
2. Clique em **Abrir FinOps e conectar**.
3. Entre no FinOps, confirme o autenticador e confira o código exibido pelo instalador.
4. Escolha a empresa, leia as permissões e clique em **Autorizar conexão**.
5. Volte ao assistente. Ele só confirma a conexão depois de consultar a empresa e as contas.
6. No Claude Code, reabra a sessão e use `/mcp`. O servidor aparece como `finops-` seguido de parte do identificador da empresa.

Se não houver contas ou lançamentos, a consulta pode retornar vazia. Isso não significa falha de instalação nem cria uma conexão bancária. O Open Finance precisa ser configurado no FinOps, com o consentimento bancário correspondente.

## Cole isto no agente de código

```text
Instale o FinOps Connect neste computador a partir do repositório
https://github.com/pedromagnago/fullbpo-claude, release connect-v0.1.0.

Antes, confirme comigo: Claude Code ou integração por API; empresa que pretendo
consultar; se já tenho acesso ao FinOps e ao autenticador. Detecte o sistema e a
arquitetura. Não peça minha senha, token ou código de autenticação no chat.

Leia installer/README.md da tag connect-v0.1.0. Baixe o ZIP compatível e seu
arquivo .sha256 na release. Confira SHA-256 antes de extrair e executar.
Não use um pacote de outra arquitetura. Não altere outros servidores MCP.
Não instale o plugin antigo que depende do Google Drive.

Abra o FinOps Connect e deixe o login e a autorização comigo, no navegador.
Depois de eu autorizar, confirme o servidor no Claude Code com /mcp ou
claude mcp get <nome exibido pelo instalador>. Peça ao MCP finops_empresa
e uma consulta de finops_contas. Mostre a empresa e se a consulta funcionou,
sem tratar uma lista vazia como erro. Se houver bloqueio, apresente a mensagem
exata e o passo necessário. Não contorne a autenticação nem permissões.

Para API, a exportação da credencial é minha ação no assistente. Nunca leia
ou imprima o token no chat. Configure o servidor para lê-lo de um cofre ou
arquivo privado fora do repositório, seguindo installer/API.md.
```

## Revogar ou trocar a conexão

Abra [Minhas conexões no FinOps](https://os.fullbpo.com/conectar-agente/) com a mesma conta e clique em **Revogar acesso**. A próxima chamada será recusada. Desinstalar o programa ou remover o MCP do Claude não revoga a credencial no servidor.

Cada autorização vale por 90 dias e por uma empresa. Para outra empresa, execute novamente e selecione-a. Cada empresa tem um servidor MCP separado. Ao renovar uma conexão da mesma empresa, revogue a anterior na tela do FinOps.

## Diagnóstico

- **Código expirou:** reinicie a conexão; o código vale por dez minutos.
- **Empresa não aparece:** confira o e-mail da conta e peça revisão do vínculo à FullBPO.
- **Primeiro acesso:** use o convite recebido ou a opção de definir senha no FinOps; depois volte ao instalador.
- **Claude Code não encontrado:** a credencial pode ter sido salva; instale/abra o Claude Code e rode o assistente novamente.
- **Cofre indisponível:** use sua sessão normal do Windows/macOS. Não há fallback para guardar segredo em texto aberto.
- **Sem resposta:** confira a internet. O assistente não confirma sucesso quando a consulta falha.
- **Credencial vencida ou revogada:** autorize uma nova conexão.

O comando `FinOpsConnect doctor --profile <id-da-empresa>` imprime apenas o resultado do teste, sem segredos. A credencial fica no cofre do sistema (`com.fullbpo.finops-connect`); os metadados e a cópia do executável ficam em `~/.fullbpo/connect`.

## Desenvolvimento

Com `uv` instalado: `uv sync --project installer --frozen --group build` e
`uv run --project installer python installer/finops_connect.py`.
Testes: `uv run --project installer python -m unittest discover -s installer -p 'test_*.py'`.
O workflow `.github/workflows/finops-connect.yml` gera os três pacotes, testa o comando de versão e publica as tags `connect-v*` como pré-release.
