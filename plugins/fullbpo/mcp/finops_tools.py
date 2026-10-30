"""Operação FinOps com o Claude e a sessão do próprio membro do time."""
from __future__ import annotations

import uuid
import json
from pathlib import Path
import finops_client


def ferramentas(busca: str = '', ferramenta: str | None = None) -> dict:
    """Descobre o catálogo em uso, com schema completo sob demanda."""
    tools = finops_client.catalogo()
    if ferramenta:
        matches = [t for t in tools if t['name'] == ferramenta]
        if not matches:
            raise finops_client.FinOpsToolError('Ferramenta não encontrada no catálogo atual.')
        return {'ferramentas': matches}
    needle = busca.casefold()
    return {'ferramentas': [
        {k: t[k] for k in ('name', 'description', 'mode', 'risk', 'readActions') if k in t}
        for t in tools if needle in (t['name'] + ' ' + t.get('description', '')).casefold()
    ], 'orientacao': 'Para saber onde acompanhar ou como realizar um fluxo, consulte finops_mapa. Peça o schema pelo nome antes de executar. pending=true significa que nada foi executado.'}


def executar(ferramenta: str, parametros: dict | None = None, cliente: str | None = None) -> dict:
    """Executa exclusivamente ferramentas do catálogo autenticado, pelo gate do FinOps."""
    tool = next((t for t in finops_client.catalogo() if t['name'] == ferramenta), None)
    if not tool:
        raise finops_client.FinOpsToolError('Ferramenta não encontrada. Consulte finops_ferramentas.')
    params = dict(parametros or {})
    if 'acting_user_id' in params:
        raise finops_client.FinOpsToolError('A identidade vem do login; não informe acting_user_id.')
    if cliente:
        cid = finops_client.resolver_company_id(cliente)
        if params.get('company_id') and params['company_id'] != cid:
            raise finops_client.FinOpsToolError('cliente e company_id apontam para empresas diferentes.')
        params['company_id'] = cid
    properties = tool.get('inputSchema', {}).get('properties', {})
    if 'dry_run' in properties:
        params.setdefault('dry_run', True)
    if ferramenta == 'manage_tarefas' and params.get('action') == 'criar':
        params.setdefault('tarefa_id', str(uuid.uuid4()))
    try:
        return finops_client.request({'tool': ferramenta, 'params': params})
    except finops_client.FinOpsToolError as error:
        return {'success': False, 'tool': ferramenta, **error.details}


def decidir(token: str, aprovar: bool, confirmacao_humana: bool = False) -> dict:
    """A confirmação é da pessoa; nunca é produzida automaticamente pelo Claude."""
    if not token or not isinstance(token, str):
        raise finops_client.FinOpsToolError('Informe o token da pendência retornada pelo FinOps.')
    op = 'aprovar_pendencia' if aprovar else 'rejeitar_pendencia'
    if not confirmacao_humana:
        return {'dry_run': True, 'op': op, 'token': token,
                'message': 'Apresente a pendência à pessoa. Só envie confirmacao_humana=true após a decisão explícita dela para esta pendência.'}
    return finops_client.request({'op': op, 'token': token})


def contexto(cliente: str | None = None) -> dict:
    result = executar('finops_contexto', {}, cliente)
    manifest = Path(__file__).resolve().parents[1] / '.claude-plugin/plugin.json'
    result['plugin'] = {'versao': json.loads(manifest.read_text(encoding='utf-8'))['version']}
    return result


def register(mcp):
    @mcp.tool()
    def finops_contexto(cliente: str | None = None) -> dict:
        """Comece aqui: identifica o login, escopo, versões e restrições. Não testa ERP nem grava dados. Informe cliente para confirmar acesso à empresa. Não confunda catálogo disponível com autorização ou saúde de integração."""
        return contexto(cliente)

    @mcp.tool()
    def finops_mapa(busca: str = '', cliente: str | None = None) -> dict:
        """Onde vejo isso? Como faço? Mapa oficial de telas, caminhos, operações, limites e ferramentas do FinOps. Consulte por objetivo (onboarding, fechamento, conciliação, tarefas). Não procure o código do FinOps na pasta do cliente nem invente menus."""
        return executar('finops_mapa', {'busca': busca}, cliente)

    @mcp.tool()
    def finops_implantacao(cliente: str, action: str = 'consultar', parametros: dict | None = None) -> dict:
        """Checklist operacional de implantação: etapas, observações, progresso e caminho da tela. Disponível à equipe na carteira autorizada, sem contratos comerciais. Atualizar_etapa exige ids, versão, status e observação; começa em prévia e confirma por nova leitura. Duplicidades exigem revisão, nunca escolha ou exclua cópias automaticamente."""
        p = dict(parametros or {})
        p['action'] = action
        return executar('manage_implantacao', p, cliente)

    @mcp.tool()
    def finops_ferramentas(busca: str = '', ferramenta: str | None = None) -> dict:
        """Catálogo ATUAL completo do FinOps. Busca por assunto; ferramenta retorna schema e exemplo. Inclui escrita, CRM, onboarding, tarefas, conciliação e conhecimento, conforme permissões do login."""
        return ferramentas(busca, ferramenta)

    @mcp.tool()
    def finops_executar(ferramenta: str, parametros: dict | None = None, cliente: str | None = None) -> dict:
        """Executa uma ferramenta descoberta em finops_ferramentas, com o próprio login. Escritas com dry_run começam como prévia. pending=true NÃO é execução: mostre a pendência e aguarde decisão humana. Não aprove automaticamente. Para executar o trabalho com este Claude use manage_tarefas e registrar_na_tarefa; manage_trabalho_ia.iniciar chama o motor de IA do servidor e só deve ser usado quando solicitado."""
        return executar(ferramenta, parametros, cliente)

    @mcp.tool()
    def finops_decidir_pendencia(token: str, aprovar: bool, confirmacao_humana: bool = False) -> dict:
        """Aprova/rejeita uma pendência SOMENTE após decisão explícita da pessoa para esse token. O padrão apenas mostra uma prévia. Mantém autorização, auditoria e bloqueio de identidades de agente no servidor."""
        return decidir(token, aprovar, confirmacao_humana)

    @mcp.tool()
    def finops_tarefas(cliente: str, action: str = 'listar', parametros: dict | None = None) -> dict:
        """Tarefas do quadro: listar, consultar, criar, atualizar, atualizar_item. Consulte o schema manage_tarefas para parâmetros. Este Claude executa o trabalho; nenhuma outra IA é acionada. Atualizar exige versao=updated_at. Concluir exige evidência. Criação em prévia devolve tarefa_id: reutilize-o na execução e em retries."""
        p = dict(parametros or {})
        p['action'] = action
        return executar('manage_tarefas', p, cliente)

    @mcp.tool()
    def finops_onboarding(busca: str = '', cliente: str | None = None, action: str = 'consultar', parametros: dict | None = None) -> dict:
        """Consulta comercial ADMINISTRATIVA: proposta, contrato existente e etapas, mesmo antes do cadastro da empresa. Para a equipe acompanhar checklist da carteira use finops_implantacao; para telas e caminhos use finops_mapa. D4Sign usa a conexão do FinOps; não requer credencial local. conferir_assinatura pode concluir conversão se assinado; atualizar_etapa registra avanço. Escritas começam como prévia. Nunca cria outro contrato por falta de token no plugin D4Sign local."""
        p = dict(parametros or {})
        p['action'] = action
        if busca:
            p['busca'] = busca
        return executar('comercial_onboarding', p, cliente)
