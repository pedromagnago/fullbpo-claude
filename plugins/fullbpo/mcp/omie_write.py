"""Omie ERP — tools de ESCRITA, via FinOps (fase 2 do blueprint).

Espelho de escrita do omie.py. Cada função é um atalho fino sobre a MESMA Edge
Function `mcp-server` (finops_client.call_tool), mas mirando as tools de ESCRITA
do Omie. Três travas herdadas do servidor, que o plugin NÃO afrouxa:

  1. dry_run=True por PADRÃO. Sem dry_run=False explícito, a chamada só devolve o
     PREVIEW (idempotency_key + endpoint + param), sem tocar na Omie. O fluxo é
     sempre: previsualize → humano confere → reenvia com dry_run=False.
  2. Gate de admin FullBPO no servidor: só admin escreve na Omie pela porta MCP
     (mesma segurança da leitura — o JWT do operador manda; a carteira decide).
  3. Anti-eco no servidor (idempotência determinística + carimbo + ledger), pra um
     reenvio idêntico nunca virar 2º título (incidente dos 51 títulos-fantasma).

`cliente` = NOME (resolvido em finops_empresas.json) OU company_id (UUID) direto.
"""
from __future__ import annotations

import finops_client as _fc


def _cid(cliente: str) -> str:
    return _fc.resolver_company_id(cliente)


def _limpar(d: dict) -> dict:
    # remove só os None; dry_run (bool) é sempre preservado, inclusive False
    return {k: v for k, v in d.items() if v is not None}


# ─── Contas a Pagar (CPA) ────────────────────────────────────────────────────
def incluir_conta_pagar(cliente: str, codigo_cliente_fornecedor: int,
                        valor_documento: float, data_vencimento: str,
                        codigo_categoria: str, id_conta_corrente: int,
                        data_previsao: str | None = None, data_emissao: str | None = None,
                        numero_documento: str | None = None, numero_parcela: str | None = None,
                        observacao: str | None = None, finops_id: str | None = None,
                        dry_run: bool = True) -> dict:
    return _fc.call_tool("omie_incluir_conta_pagar", _limpar({
        "company_id": _cid(cliente),
        "codigo_cliente_fornecedor": codigo_cliente_fornecedor,
        "valor_documento": valor_documento,
        "data_vencimento": data_vencimento,
        "codigo_categoria": codigo_categoria,
        "id_conta_corrente": id_conta_corrente,
        "data_previsao": data_previsao,
        "data_emissao": data_emissao,
        "numero_documento": numero_documento,
        "numero_parcela": numero_parcela,
        "observacao": observacao,
        "finops_id": finops_id,
        "dry_run": dry_run,
    }))


def alterar_conta_pagar(cliente: str, codigo_lancamento_omie: int,
                        valor_documento: float | None = None, data_vencimento: str | None = None,
                        data_previsao: str | None = None, codigo_categoria: str | None = None,
                        codigo_cliente_fornecedor: int | None = None,
                        id_conta_corrente: int | None = None, numero_documento: str | None = None,
                        observacao: str | None = None, dry_run: bool = True) -> dict:
    return _fc.call_tool("omie_alterar_conta_pagar", _limpar({
        "company_id": _cid(cliente),
        "codigo_lancamento_omie": codigo_lancamento_omie,
        "valor_documento": valor_documento,
        "data_vencimento": data_vencimento,
        "data_previsao": data_previsao,
        "codigo_categoria": codigo_categoria,
        "codigo_cliente_fornecedor": codigo_cliente_fornecedor,
        "id_conta_corrente": id_conta_corrente,
        "numero_documento": numero_documento,
        "observacao": observacao,
        "dry_run": dry_run,
    }))


def excluir_conta_pagar(cliente: str, codigo_lancamento_omie: int,
                        dry_run: bool = True) -> dict:
    return _fc.call_tool("omie_excluir_conta_pagar", {
        "company_id": _cid(cliente),
        "codigo_lancamento_omie": codigo_lancamento_omie,
        "dry_run": dry_run,
    })


# ─── Contas a Receber (CRE) ──────────────────────────────────────────────────
def incluir_conta_receber(cliente: str, codigo_cliente_fornecedor: int,
                          valor_documento: float, data_vencimento: str,
                          codigo_categoria: str, id_conta_corrente: int,
                          data_previsao: str | None = None, data_emissao: str | None = None,
                          numero_documento: str | None = None, numero_parcela: str | None = None,
                          observacao: str | None = None, finops_id: str | None = None,
                          dry_run: bool = True) -> dict:
    return _fc.call_tool("omie_incluir_conta_receber", _limpar({
        "company_id": _cid(cliente),
        "codigo_cliente_fornecedor": codigo_cliente_fornecedor,
        "valor_documento": valor_documento,
        "data_vencimento": data_vencimento,
        "codigo_categoria": codigo_categoria,
        "id_conta_corrente": id_conta_corrente,
        "data_previsao": data_previsao,
        "data_emissao": data_emissao,
        "numero_documento": numero_documento,
        "numero_parcela": numero_parcela,
        "observacao": observacao,
        "finops_id": finops_id,
        "dry_run": dry_run,
    }))


def alterar_conta_receber(cliente: str, codigo_lancamento_omie: int,
                          valor_documento: float | None = None, data_vencimento: str | None = None,
                          data_previsao: str | None = None, codigo_categoria: str | None = None,
                          codigo_cliente_fornecedor: int | None = None,
                          id_conta_corrente: int | None = None, numero_documento: str | None = None,
                          observacao: str | None = None, dry_run: bool = True) -> dict:
    return _fc.call_tool("omie_alterar_conta_receber", _limpar({
        "company_id": _cid(cliente),
        "codigo_lancamento_omie": codigo_lancamento_omie,
        "valor_documento": valor_documento,
        "data_vencimento": data_vencimento,
        "data_previsao": data_previsao,
        "codigo_categoria": codigo_categoria,
        "codigo_cliente_fornecedor": codigo_cliente_fornecedor,
        "id_conta_corrente": id_conta_corrente,
        "numero_documento": numero_documento,
        "observacao": observacao,
        "dry_run": dry_run,
    }))


def excluir_conta_receber(cliente: str, codigo_lancamento_omie: int,
                          dry_run: bool = True) -> dict:
    return _fc.call_tool("omie_excluir_conta_receber", {
        "company_id": _cid(cliente),
        "codigo_lancamento_omie": codigo_lancamento_omie,
        "dry_run": dry_run,
    })


# ─── Baixa (liquidação de título) ────────────────────────────────────────────
def baixar_titulo(cliente: str, tipo: str, codigo_lancamento_omie: int,
                  valor: float | None = None, data: str | None = None,
                  id_conta_corrente: int | None = None, juros: float | None = None,
                  desconto: float | None = None, multa: float | None = None,
                  observacao: str | None = None, omie_endpoint: str | None = None,
                  omie_call: str | None = None, dry_run: bool = True) -> dict:
    return _fc.call_tool("omie_baixar_titulo", _limpar({
        "company_id": _cid(cliente),
        "tipo": tipo,
        "codigo_lancamento_omie": codigo_lancamento_omie,
        "valor": valor,
        "data": data,
        "id_conta_corrente": id_conta_corrente,
        "juros": juros,
        "desconto": desconto,
        "multa": multa,
        "observacao": observacao,
        "omie_endpoint": omie_endpoint,
        "omie_call": omie_call,
        "dry_run": dry_run,
    }))


# ─── Cadastro de Cliente/Fornecedor ──────────────────────────────────────────
def incluir_cliente_fornecedor(cliente: str, razao_social: str, cnpj_cpf: str,
                               papel: str | None = None, nome_fantasia: str | None = None,
                               email: str | None = None, pessoa_fisica: str | None = None,
                               inativo: str | None = None, finops_id: str | None = None,
                               dry_run: bool = True) -> dict:
    return _fc.call_tool("omie_incluir_cliente_fornecedor", _limpar({
        "company_id": _cid(cliente),
        "razao_social": razao_social,
        "cnpj_cpf": cnpj_cpf,
        "papel": papel,
        "nome_fantasia": nome_fantasia,
        "email": email,
        "pessoa_fisica": pessoa_fisica,
        "inativo": inativo,
        "finops_id": finops_id,
        "dry_run": dry_run,
    }))


def alterar_cliente_fornecedor(cliente: str, codigo_cliente_omie: int,
                               razao_social: str | None = None, nome_fantasia: str | None = None,
                               email: str | None = None, inativo: str | None = None,
                               dry_run: bool = True) -> dict:
    return _fc.call_tool("omie_alterar_cliente_fornecedor", _limpar({
        "company_id": _cid(cliente),
        "codigo_cliente_omie": codigo_cliente_omie,
        "razao_social": razao_social,
        "nome_fantasia": nome_fantasia,
        "email": email,
        "inativo": inativo,
        "dry_run": dry_run,
    }))
