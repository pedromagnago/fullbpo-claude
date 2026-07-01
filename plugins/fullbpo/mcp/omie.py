"""Omie ERP — agora via FinOps (engine multi-tenant na nuvem).

Fase 1 do blueprint: este módulo NÃO chama mais o Omie direto. Cada função é um
atalho fino sobre a Edge Function `mcp-server` do FinOps (finops_client),
que guarda as chaves no Vault, valida o escopo do operador (carteira) e devolve
só o dado — auditado. Continua SÓ-LEITURA: as tools de escrita do Omie não estão
expostas aqui (virão na fase 2, atrás de confirmação humana).

Toda função aceita `cliente` = NOME (resolvido em finops_empresas.json) OU o
company_id (UUID) direto.
"""
from __future__ import annotations

import finops_client as _fc


def _cid(cliente: str) -> str:
    return _fc.resolver_company_id(cliente)


def _limpar(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def test_connection(cliente: str) -> dict:
    """Testa as credenciais Omie do cliente (lidas do Vault do FinOps)."""
    return _fc.call_tool("omie_test_connection", {"company_id": _cid(cliente)})


def contas_a_pagar(cliente: str, data_de: str | None = None,
                   data_ate: str | None = None, status: str | None = None,
                   alterado_em: str | None = None, pagina: int = 1,
                   registros_por_pagina: int = 50) -> dict:
    """Contas a PAGAR (AP). status: ABERTO|PAGO|VENCIDO|CANCELADO|TODOS. Datas yyyy-MM-dd."""
    return _fc.call_tool("omie_listar_contas_pagar", _limpar({
        "company_id": _cid(cliente),
        "pagina": pagina,
        "registros_por_pagina": registros_por_pagina,
        "filtrar_por_data_de": data_de,
        "filtrar_por_data_ate": data_ate,
        "filtrar_por_status_titulo": status,
        "filtrar_apenas_alterado_em": alterado_em,
    }))


def contas_a_receber(cliente: str, data_de: str | None = None,
                     data_ate: str | None = None, status: str | None = None,
                     alterado_em: str | None = None, pagina: int = 1,
                     registros_por_pagina: int = 50) -> dict:
    """Contas a RECEBER (AR). status: A_RECEBER|RECEBIDO|VENCIDO|CANCELADO|TODOS. Datas yyyy-MM-dd."""
    return _fc.call_tool("omie_listar_contas_receber", _limpar({
        "company_id": _cid(cliente),
        "pagina": pagina,
        "registros_por_pagina": registros_por_pagina,
        "filtrar_por_data_de": data_de,
        "filtrar_por_data_ate": data_ate,
        "filtrar_por_status_titulo": status,
        "filtrar_apenas_alterado_em": alterado_em,
    }))


def listar_extrato(cliente: str, n_cod_cc: int, data_inicial: str,
                   data_final: str, pagina: int = 1,
                   registros_por_pagina: int = 100) -> dict:
    """Extrato de UMA conta corrente (n_cod_cc) no período. Datas yyyy-MM-dd."""
    return _fc.call_tool("omie_listar_extrato", {
        "company_id": _cid(cliente),
        "nCodCC": n_cod_cc,
        "dDtInicial": data_inicial,
        "dDtFinal": data_final,
        "pagina": pagina,
        "registros_por_pagina": registros_por_pagina,
    })


def listar_categorias(cliente: str, pagina: int = 1,
                      registros_por_pagina: int = 100) -> dict:
    """Plano de categorias do Omie (estrutura de classificação financeira)."""
    return _fc.call_tool("omie_listar_categorias", {
        "company_id": _cid(cliente),
        "pagina": pagina,
        "registros_por_pagina": registros_por_pagina,
    })


def listar_clientes_fornecedores(cliente: str, apenas_cliente: bool = False,
                                 apenas_fornecedor: bool = False,
                                 apenas_importado_api: str = "N", pagina: int = 1,
                                 registros_por_pagina: int = 50) -> dict:
    """Cadastro de clientes/fornecedores do Omie do cliente."""
    return _fc.call_tool("omie_listar_clientes_fornecedores", _limpar({
        "company_id": _cid(cliente),
        "apenas_importado_api": apenas_importado_api,
        "filtrar_por_cliente": "S" if apenas_cliente else None,
        "filtrar_por_fornecedor": "S" if apenas_fornecedor else None,
        "pagina": pagina,
        "registros_por_pagina": registros_por_pagina,
    }))


def sync_company(cliente: str, desde: str | None = None,
                 dry_run: bool = False, full_sync: bool = False) -> dict:
    """Espelha os dados do Omie do cliente na base do FinOps (sync).

    dry_run=True só simula (não grava). desde=yyyy-MM-dd limita o recorte;
    full_sync=True força recarga completa.
    """
    return _fc.call_tool("omie_sync_company", _limpar({
        "company_id": _cid(cliente),
        "desde": desde,
        "dry_run": dry_run,
        "full_sync": full_sync,
    }))
