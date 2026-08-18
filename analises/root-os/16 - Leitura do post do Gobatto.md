---
tags: [root-os, produto, oferta, conteudo, mcp, leitura]
tipo: leitura
status: rascunho
criado: 2026-08-18
fonte: "[[15 - Post do Gobatto sobre formatos (transcricao)]] · [[14 - Ofertas e esteira]] · [[00 - COMECE AQUI]]"
---

# Leitura do post do Gobatto — o que ele faz com a nossa esteira

> A leitura interna de [[15 - Post do Gobatto sobre formatos (transcricao)]], de 06/08/2026.
> Resumo do resumo: **ele descreve, do lado de fora, o degrau 0 e o degrau 3 da nossa esteira — e passa direto pelo pedaço que é só nosso.** O post não muda a arquitetura. Muda a promessa escrita do degrau 1.

---

## Estado em 18/08/2026 — leia isto primeiro

| | |
|---|---|
| **Confirma** | MCP como canal de distribuição e "entregar pronto" no lugar de "ensinar a fazer" — as duas apostas já tomadas em [[14 - Ofertas e esteira]] |
| **Expõe** | O programa/imersão dentro do degrau 1: é exatamente o formato que o post declara morto |
| **Não muda** | Preço, degraus, escada R0–R5, arquitetura das 4 camadas |
| **Falta medir** | Consultas ao método via IA do cliente vs. aulas assistidas — o experimento dele, rodado na nossa base |
| **Ação externa** | Responder o post é **R3**: proposta pronta abaixo, envio depende de aprovação |

---

## A tese dele em uma frase

**Todo formato de conteúdo até hoje cobrou a mesma coisa — parar. O que vem depois não é conteúdo melhor: é conteúdo que chega dentro da ferramenta onde a pessoa já está, ou trabalho já feito e entregue.**

Os dois caminhos que ele enxerga:

| # | Caminho | Como ele descreve |
|---|---|---|
| 1 | O conteúdo vai até a IA que a pessoa já usa | Plugou o curso no Claude do aluno, com a conta e o modelo do aluno. "Isso se chama MCP" |
| 2 | Menos curso, mais serviço entregue | "Em vez de vender a instrução e torcer pra pessoa executar, você executa e entrega pronto" |

---

## Onde ele confirma decisão que já era nossa

| O que ele diz | O que já está escrito aqui |
|---|---|
| Chat dentro da plataforma do produtor não sobrevive: a IA sai barata porque quem paga é o produtor, ela não conhece o aluno, e é brigar com quem constrói IA | Nosso conteúdo nunca morou em chat próprio. O plugin `fullbpo` roda na licença do cliente — "os conectores não vêm no plugin, cada pessoa conecta na própria conta" |
| Inverter a ordem: plugar o produto no Claude de quem consome | Degrau 0 e degrau 1 de [[14 - Ofertas e esteira]] — repo aberto e instância com MEMÓRIA + conectores OAuth |
| Entregar em escala o que dependia de hora humana | Degraus 2 e 3 — catálogo de agentes e implantação assistida |
| "Os dois tiram o peso do assistir" | A frase de fecho do [[00 - COMECE AQUI]] já é *"Pare de assistir. Comece a operar."* |

Duas pessoas chegando na mesma frase, por caminhos diferentes, em semanas diferentes, é o sinal mais forte do post. **Não é ideia nova nossa; é ideia que está no ar.** Isso corta o prazo de vantagem: o argumento de venda do degrau 0 vale mais este semestre do que no ano que vem.

---

## Onde ele bate no ponto fraco

O degrau 1 vende, hoje, três coisas juntas: **software + programa de onboarding + crew no 1º ano**. O post é uma tese contra o pedaço do meio.

| Peça do degrau 1 | Passa no teste "não pede pra parar"? |
|---|---|
| Instância no ar, painel, graph | passa — é ferramenta, não aula |
| MEMÓRIA carregada com o negócio | passa — é o conteúdo indo até a IA dele |
| Escada R0–R5 configurada, RASTRO em tela | passa |
| **Programa de onboarding** | **não passa** — é videoaula com outro nome |
| **Crew (encontros mensais)** | passa com ressalva: encontro é rede, não instrução; vender como rede, não como conteúdo |
| Imersão presencial (degrau 3) | não passa como *ensino*; sobrevive como *instalação assistida* — é serviço entregue, não aula |

O que fazer não é matar o programa. É mudar o suporte dele: **o método precisa nascer consultável de dentro da IA do cliente** — skill e MCP, como o plugin `fullbpo` já faz com os 58 agentes — e a aula vira o resíduo, não o produto. A nota [[08 - Perguntas ao acervo de videos]] foi arquivada; o post ressuscita a pergunta dela com outro enquadramento: o acervo não é para assistir, é para o agente do cliente consultar.

---

## O degrau que ele não tem

Ele plugou **conteúdo** no Claude do aluno. Nós plugamos **ação** — e ação precisa de trava.

| Camada | Ele | Nós |
|---|---|---|
| Conteúdo consultável via MCP | tem | tem |
| Contexto do negócio do cliente (MEMÓRIA) | não | tem |
| Número com procedência (ESPELHO) | não | tem |
| Decisão antes do modelo agir (POLÍTICA + PORTEIRO) | não | tem, em código |
| Prova depois (RASTRO) | não | especificado |

É a diferença entre *"o curso responde dentro do seu Claude"* e *"a sua operação executa dentro do seu Claude, com trava e registro"*. **O post é a melhor peça de venda que já apareceu para o nosso degrau 0 — porque para quem comprar a tese dele, o próximo passo natural é o nosso degrau 1.**

---

## O que não copiar

1. **O número dele não é número.** 7 pessoas, um mês, sem denominador, e ele mesmo diz que não é lei. Serve como sinal, nunca como argumento de venda com dado.
2. **O negócio é outro.** A margem dele está no conteúdo; a nossa está na instância mais assinatura ([[14 - Ofertas e esteira]]). "Menos curso, mais serviço" já é a nossa posição de origem — não é virada, é confirmação.
3. **Não trocar a esteira por causa de um post.** As duas regras que sustentam a esteira continuam de pé: cada degrau entrega resultado sozinho, e a permissão sobe junto com o degrau.

---

## O que dá para fazer nesta semana

| # | Ação | Por que agora |
|---|---|---|
| A-1 | Rodar o experimento dele na nossa base: instrumentar **consultas ao método via MCP** vs. **aulas/material assistido**, mesma janela, mesma base | É o único jeito de trocar a tese emprestada por número próprio. E casa com o RASTRO, que já precisa virar tela |
| A-2 | Reescrever a promessa do degrau 1: sai "programa de onboarding", entra **"o método fica consultável dentro da sua IA"** | Ajuste de texto, custo zero, e tira do material a peça que o mercado está descartando |
| A-3 | Empacotar o programa como skill + MCP no padrão do plugin `fullbpo` (58 agentes, 3 skills de método já são precedente) | Transforma conteúdo parado em capacidade instalada — vira ativo do degrau 1, não bônus |
| A-4 | Guardar o post como peça de topo: ele descreve o problema; o nosso degrau 0 é a resposta | Distribuição barata, sem produzir nada novo |

---

## Ação externa — proposta de resposta ao post (**R3, precisa de aprovação**)

Ele pediu resposta nos comentários. Isso é envio externo em nome da marca: pela escada, **não sai sem aprovação humana do conteúdo exato**. Rascunho pronto:

> Aposto no segundo, e acho que os dois são o mesmo caminho em fases. O conteúdo entrar via MCP é o começo: a IA passa a responder com o contexto do negócio. O passo seguinte é ela **executar** com trava — o que pode fazer sozinha, o que para em rascunho, o que exige aprovação. Aí o formato deixa de ser conteúdo e vira sistema instalado. Aqui a gente foi por esse lado desde o início: o cliente usa a licença dele, o método entra como skill, e a régua do que a IA pode fazer é o que separa um degrau do outro.

Se aprovar, sai como resposta no post; se não, o texto vale igual como parágrafo do degrau 0.

---

## O que ainda depende de você

| # | Decisão | Impacto |
|---|---|---|
| C-1 | O programa do degrau 1 vira **consultável** (skill/MCP) ou continua **assistível** (aulas) | Define se o degrau 1 envelhece junto com o formato videoaula |
| C-2 | A imersão presencial é reposicionada como **instalação assistida** (serviço) em vez de treinamento | Muda o material de venda do degrau 3, não o escopo |
| C-3 | Medir A-1 na nossa base — e com qual instrumento, já que o RASTRO ainda não é tela | Sem isso, seguimos usando o número de outra pessoa |
| C-4 | Publicar ou não a resposta no post | É R3; o conteúdo acima está pronto para aprovação |

---

## Relacionado

- [[15 - Post do Gobatto sobre formatos (transcricao)]] — a fonte, íntegra
- [[14 - Ofertas e esteira]] — os cinco degraus; o post tensiona o 1 e reforça o 0 e o 3
- [[00 - COMECE AQUI]] — arquitetura das 4 camadas, e a frase que o post repete sem saber
- [[09 - Escada de risco R0-R5]] — a régua que classifica a resposta pública como R3
- [[12 - Conversa com Lucas (transcricao)]] — mesma discussão pelo lado da proposta de valor
- [[08 - Perguntas ao acervo de videos]] — arquivada; o post reabre a pergunta com outro enquadramento

**Ele descreveu a porta. A trava é nossa.**
