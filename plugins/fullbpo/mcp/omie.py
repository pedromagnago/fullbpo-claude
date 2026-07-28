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


def listar_contas_correntes(cliente: str, pagina: int = 1,
                            registros_por_pagina: int = 100) -> dict:
    """Contas correntes (banco/caixa/aplicação) do cliente no Omie (só-leitura).

    Devolve o nCodCC de cada conta — o código que omie_listar_extrato (n_cod_cc) e
    TODA tool de escrita (id_conta_corrente) exigem, e que até aqui nenhuma outra
    tool revelava. É o elo que faltava na cadeia leitura→escrita.
    """
    return _fc.call_tool("omie_listar_contas_correntes", {
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


# ─── Posição financeira (agregador SÓ-LEITURA — compõe as leituras acima) ─────
# Não chama nenhuma tool nova no servidor: usa omie_contas_a_pagar/receber, que
# já existem. Por isso é a fatia 100% construível no plugin, sem dependência
# server-side. Regra de ouro respeitada: NUNCA inventa dado — título que não
# parsear entra em contador próprio (nada some em silêncio).
_MAX_PAGINAS = 40  # teto anti-loop por lado; sinaliza truncado=True se estourar


def _brl(v: float) -> str:
    """Formata como moeda pt-BR: 1234.5 → 'R$ 1.234,50'."""
    return "R$ " + f"{v:,.2f}".replace(",", "·").replace(".", ",").replace("·", ".")


def _num(x) -> float | None:
    """Coerção defensiva p/ float. Omie devolve número JSON; strings são fallback.
    Devolve None se não der pra interpretar (em vez de chutar 0)."""
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return None
        if "," in s and "." in s:      # 1.234,56 → 1234.56
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:                  # 1234,56 → 1234.56
            s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _venc_no_passado(data_venc: str) -> bool | None:
    """True se dd/mm/aaaa < hoje; False se >= hoje; None se não parsear."""
    from datetime import date
    try:
        d, m, a = (int(p) for p in str(data_venc).split("/"))
        return date(a, m, d) < date.today()
    except (ValueError, AttributeError):
        return None


def _registros(resp: dict) -> list:
    """Extrai a lista de títulos sem cravar a chave (conta_pagar_cadastro /
    conta_receber_cadastro): pega a 1ª lista do dict de resposta."""
    if not isinstance(resp, dict):
        return []
    for v in resp.values():
        if isinstance(v, list):
            return v
    return []


def _somar_lado(fetch, cliente: str) -> dict:
    """Pagina um lado (AP ou AR) somando o saldo dos títulos ABERTOS por bucket
    vencido / a_vencer. `fetch` é contas_a_pagar ou contas_a_receber."""
    vencido = a_vencer = 0.0
    qtd = sem_valor = sem_data = 0
    pagina, truncado = 1, False
    while True:
        resp = fetch(cliente, status="ABERTO", pagina=pagina,
                     registros_por_pagina=200)
        for r in _registros(resp):
            qtd += 1
            val = _num(r.get("saldo_titulo"))
            if val is None:
                val = _num(r.get("valor_documento"))
            if val is None:
                sem_valor += 1
                continue
            passou = _venc_no_passado(r.get("data_vencimento", ""))
            if passou is None:
                sem_data += 1
                a_vencer += val        # sem data → conservador: trata como a vencer
            elif passou:
                vencido += val
            else:
                a_vencer += val
        total_pag = resp.get("total_de_paginas") or 1
        if pagina >= total_pag:
            break
        pagina += 1
        if pagina > _MAX_PAGINAS:
            truncado = True
            break
    return {"vencido": round(vencido, 2), "a_vencer": round(a_vencer, 2),
            "total": round(vencido + a_vencer, 2), "qtd_titulos": qtd,
            "titulos_sem_valor": sem_valor, "titulos_sem_data": sem_data,
            "truncado": truncado}


def posicao_financeira(cliente: str) -> dict:
    """Snapshot de caixa do cliente (agregador SÓ-LEITURA, client-side).

    Compõe contas_a_pagar + contas_a_receber (títulos ABERTOS), somando por bucket
    vencido / a_vencer, e devolve a posição líquida de títulos. Não inclui saldo
    bancário — só títulos. Título sem valor/data reconhecível entra em contador
    próprio (titulos_sem_valor / titulos_sem_data), nunca some em silêncio;
    truncado=True avisa se houve mais páginas que o teto de segurança.
    """
    ap = _somar_lado(contas_a_pagar, cliente)
    ar = _somar_lado(contas_a_receber, cliente)
    liquido = round(ar["total"] - ap["total"], 2)
    return {
        "cliente": cliente,
        "a_pagar": ap,
        "a_receber": ar,
        "posicao_liquida_titulos": liquido,
        "resumo_fmt": (
            f"A pagar {_brl(ap['total'])} (vencido {_brl(ap['vencido'])}) · "
            f"A receber {_brl(ar['total'])} (vencido {_brl(ar['vencido'])}) · "
            f"Líquido {_brl(liquido)}"
        ),
        "_nota": ("Posição de TÍTULOS abertos (não inclui saldo bancário). "
                  "Saldo em conta corrente entra quando o servidor confirmar "
                  "omie_listar_contas_correntes."),
    }
