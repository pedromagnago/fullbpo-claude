# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2.0", "httpx>=0.28", "python-dotenv>=1.0"]
# ///
"""Servidor MCP slim do plugin FullBPO — Omie/FinOps (leitura + escrita).

Empacota, DENTRO do plugin distribuível, as tools que hoje vivem no servidor
completo local do Pedro. Sobe com `uv run --script` (venv efêmero, Python ≥3.10
resolvido sozinho); o dir deste script entra no sys.path[0], então os imports
são flat: config / finops_client / omie / omie_write são os irmãos aqui em mcp/.

  config         → descobre a pasta FullBPO-MCP no Drive + identidade local
  finops_client  → login do operador (JWT), refresh, bridge p/ a Edge Function
  omie           → atalhos finos das tools omie_* (só-leitura)
  omie_write     → atalhos das tools de ESCRITA (dry_run=True por padrão)

ESCRITA: toda tool de escrita nasce com dry_run=True — sem dry_run=False
explícito, o servidor só devolve o PREVIEW (nada toca a Omie). O fluxo é sempre
previsualize → operador confere → reenvia com dry_run=False. As travas de fato
moram no servidor (gate de admin + anti-eco/idempotência), não neste plugin.

Segredos: nenhum vive aqui. URL + anon (publicável) + mapa nome→UUID vêm da
pasta compartilhada no Drive; e-mail/senha/sessão são locais por máquina.

Uso:
  uv run --script omie_mcp.py             → sobe o servidor MCP (stdio)
  uv run --script omie_mcp.py --selftest  → checa setup e sai (sem Claude)
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

import config
import finops_client
import omie
import omie_write

mcp = FastMCP("fullbpo-omie")


# ─── FinOps (engine Omie multi-tenant na nuvem) ──────────────────────────────
# As chaves do Omie ficam no Vault do FinOps; o plugin só repassa {tool, params}
# autenticado com o JWT do operador. Escopo por carteira é validado no servidor.
@mcp.tool()
def finops_empresas() -> list[dict]:
    """Carteira de clientes Omie disponíveis (nome → company_id), do mapa local.
    Use ISTO primeiro p/ descobrir o nome/cliente a passar nas tools omie_*."""
    return finops_client.empresas()


@mcp.tool()
def finops_status(cliente: str | None = None) -> dict:
    """Saúde do FinOps. Sem cliente: contagens gerais (empresas ativas, títulos
    pendentes). Com cliente (nome ou company_id): status daquela empresa."""
    if cliente:
        return finops_client.call_tool(
            "get_system_status",
            {"scope": "company", "company_id": finops_client.resolver_company_id(cliente)},
        )
    return finops_client.call_tool("get_system_status", {"scope": "all"})


# ─── Omie (financeiro — SÓ-LEITURA por construção, via FinOps) ────────────────
@mcp.tool()
def omie_test_connection(cliente: str) -> dict:
    """Testa a conexão Omie de um cliente (credenciais lidas do Vault do FinOps).
    Bom primeiro teste antes de listar dados. cliente = nome ou company_id (UUID)."""
    return omie.test_connection(cliente)


@mcp.tool()
def omie_contas_a_pagar(cliente: str, data_de: str | None = None,
                        data_ate: str | None = None, status: str | None = None,
                        pagina: int = 1, registros_por_pagina: int = 50) -> dict:
    """Contas a PAGAR (AP) do cliente no Omie (só-leitura). cliente = nome ou
    company_id (UUID). status: ABERTO|PAGO|VENCIDO|CANCELADO|TODOS. Datas yyyy-MM-dd."""
    return omie.contas_a_pagar(cliente, data_de=data_de, data_ate=data_ate,
                               status=status, pagina=pagina,
                               registros_por_pagina=registros_por_pagina)


@mcp.tool()
def omie_contas_a_receber(cliente: str, data_de: str | None = None,
                          data_ate: str | None = None, status: str | None = None,
                          pagina: int = 1, registros_por_pagina: int = 50) -> dict:
    """Contas a RECEBER (AR) do cliente no Omie (só-leitura). cliente = nome ou
    company_id (UUID). status: A_RECEBER|RECEBIDO|VENCIDO|CANCELADO|TODOS. Datas yyyy-MM-dd."""
    return omie.contas_a_receber(cliente, data_de=data_de, data_ate=data_ate,
                                 status=status, pagina=pagina,
                                 registros_por_pagina=registros_por_pagina)


@mcp.tool()
def omie_listar_extrato(cliente: str, n_cod_cc: int, data_inicial: str,
                        data_final: str, pagina: int = 1,
                        registros_por_pagina: int = 100) -> dict:
    """Extrato de UMA conta corrente do cliente no Omie (só-leitura). n_cod_cc =
    código interno da conta corrente. Datas yyyy-MM-dd."""
    return omie.listar_extrato(cliente, n_cod_cc=n_cod_cc, data_inicial=data_inicial,
                               data_final=data_final, pagina=pagina,
                               registros_por_pagina=registros_por_pagina)


@mcp.tool()
def omie_listar_categorias(cliente: str, pagina: int = 1,
                           registros_por_pagina: int = 100) -> dict:
    """Plano de categorias (classificação financeira) do cliente no Omie (só-leitura)."""
    return omie.listar_categorias(cliente, pagina=pagina,
                                  registros_por_pagina=registros_por_pagina)


@mcp.tool()
def omie_listar_clientes_fornecedores(cliente: str, apenas_cliente: bool = False,
                                      apenas_fornecedor: bool = False, pagina: int = 1,
                                      registros_por_pagina: int = 50) -> dict:
    """Cadastro de clientes/fornecedores do cliente no Omie (só-leitura). Filtre com
    apenas_cliente=True ou apenas_fornecedor=True."""
    return omie.listar_clientes_fornecedores(
        cliente, apenas_cliente=apenas_cliente, apenas_fornecedor=apenas_fornecedor,
        pagina=pagina, registros_por_pagina=registros_por_pagina)


@mcp.tool()
def omie_sync_company(cliente: str, desde: str | None = None,
                      dry_run: bool = False, full_sync: bool = False) -> dict:
    """Espelha (sincroniza) os dados do Omie do cliente na base do FinOps. Use
    dry_run=True p/ simular antes. desde=yyyy-MM-dd recorta o período."""
    return omie.sync_company(cliente, desde=desde, dry_run=dry_run, full_sync=full_sync)


# ─── Omie ESCRITA (via FinOps) — dry_run=True por PADRÃO ──────────────────────
# Regra de ouro: NUNCA reenvie com dry_run=False sem o operador humano conferir o
# preview. dry_run=True devolve só {idempotency_key, endpoint, param} — nada vai
# pra Omie. As travas reais (gate de admin + anti-eco) estão no servidor FinOps.
@mcp.tool()
def omie_incluir_conta_pagar(cliente: str, codigo_cliente_fornecedor: int,
                             valor_documento: float, data_vencimento: str,
                             codigo_categoria: str, id_conta_corrente: int,
                             data_previsao: str | None = None, data_emissao: str | None = None,
                             numero_documento: str | None = None, numero_parcela: str | None = None,
                             observacao: str | None = None, finops_id: str | None = None,
                             dry_run: bool = True) -> dict:
    """Inclui uma conta a PAGAR (título AP) no Omie do cliente. cliente = nome ou
    company_id. codigo_cliente_fornecedor = código Omie do fornecedor; codigo_categoria
    = código do plano de categorias; id_conta_corrente = código da conta corrente.
    Datas yyyy-MM-dd. dry_run=True (PADRÃO) só devolve preview — NADA vai pra Omie;
    confira com o operador e só então reenvie com dry_run=False."""
    return omie_write.incluir_conta_pagar(
        cliente, codigo_cliente_fornecedor=codigo_cliente_fornecedor,
        valor_documento=valor_documento, data_vencimento=data_vencimento,
        codigo_categoria=codigo_categoria, id_conta_corrente=id_conta_corrente,
        data_previsao=data_previsao, data_emissao=data_emissao,
        numero_documento=numero_documento, numero_parcela=numero_parcela,
        observacao=observacao, finops_id=finops_id, dry_run=dry_run)


@mcp.tool()
def omie_alterar_conta_pagar(cliente: str, codigo_lancamento_omie: int,
                             valor_documento: float | None = None, data_vencimento: str | None = None,
                             data_previsao: str | None = None, codigo_categoria: str | None = None,
                             codigo_cliente_fornecedor: int | None = None,
                             id_conta_corrente: int | None = None, numero_documento: str | None = None,
                             observacao: str | None = None, codigo_tipo_documento: str | None = None,
                             omie_param_extra: dict | None = None, dry_run: bool = True) -> dict:
    """Altera uma conta a PAGAR existente (por codigo_lancamento_omie). Passe só os
    campos que mudam (ao menos 1). codigo_tipo_documento troca o tipo do título
    (ex.: "BOL"→"TID"). omie_param_extra é passthrough pra qualquer outro campo nativo
    do Omie (AlterarContaPagar) não listado aqui. dry_run=True (PADRÃO) só devolve
    preview — NADA vai pra Omie; confira com o operador e só então reenvie com
    dry_run=False."""
    return omie_write.alterar_conta_pagar(
        cliente, codigo_lancamento_omie=codigo_lancamento_omie,
        valor_documento=valor_documento, data_vencimento=data_vencimento,
        data_previsao=data_previsao, codigo_categoria=codigo_categoria,
        codigo_cliente_fornecedor=codigo_cliente_fornecedor,
        id_conta_corrente=id_conta_corrente, numero_documento=numero_documento,
        observacao=observacao, codigo_tipo_documento=codigo_tipo_documento,
        omie_param_extra=omie_param_extra, dry_run=dry_run)


@mcp.tool()
def omie_excluir_conta_pagar(cliente: str, codigo_lancamento_omie: int,
                             dry_run: bool = True) -> dict:
    """Exclui uma conta a PAGAR (por codigo_lancamento_omie). Irreversível na Omie.
    dry_run=True (PADRÃO) só devolve preview — NADA vai pra Omie; confira com o
    operador e só então reenvie com dry_run=False."""
    return omie_write.excluir_conta_pagar(
        cliente, codigo_lancamento_omie=codigo_lancamento_omie, dry_run=dry_run)


@mcp.tool()
def omie_incluir_conta_receber(cliente: str, codigo_cliente_fornecedor: int,
                               valor_documento: float, data_vencimento: str,
                               codigo_categoria: str, id_conta_corrente: int,
                               data_previsao: str | None = None, data_emissao: str | None = None,
                               numero_documento: str | None = None, numero_parcela: str | None = None,
                               observacao: str | None = None, finops_id: str | None = None,
                               dry_run: bool = True) -> dict:
    """Inclui uma conta a RECEBER (título AR) no Omie do cliente. codigo_cliente_fornecedor
    = código Omie do cliente; codigo_categoria = código do plano de categorias;
    id_conta_corrente = código da conta corrente. Datas yyyy-MM-dd. dry_run=True
    (PADRÃO) só devolve preview — NADA vai pra Omie; confira com o operador e só
    então reenvie com dry_run=False."""
    return omie_write.incluir_conta_receber(
        cliente, codigo_cliente_fornecedor=codigo_cliente_fornecedor,
        valor_documento=valor_documento, data_vencimento=data_vencimento,
        codigo_categoria=codigo_categoria, id_conta_corrente=id_conta_corrente,
        data_previsao=data_previsao, data_emissao=data_emissao,
        numero_documento=numero_documento, numero_parcela=numero_parcela,
        observacao=observacao, finops_id=finops_id, dry_run=dry_run)


@mcp.tool()
def omie_alterar_conta_receber(cliente: str, codigo_lancamento_omie: int,
                               valor_documento: float | None = None, data_vencimento: str | None = None,
                               data_previsao: str | None = None, codigo_categoria: str | None = None,
                               codigo_cliente_fornecedor: int | None = None,
                               id_conta_corrente: int | None = None, numero_documento: str | None = None,
                               observacao: str | None = None, codigo_tipo_documento: str | None = None,
                               omie_param_extra: dict | None = None, dry_run: bool = True) -> dict:
    """Altera uma conta a RECEBER existente (por codigo_lancamento_omie). Passe só os
    campos que mudam (ao menos 1). codigo_tipo_documento troca o tipo do título
    (ex.: "BOL"→"TID" — boleto → título descontado). omie_param_extra é passthrough
    pra qualquer outro campo nativo do Omie (AlterarContaReceber) não listado aqui.
    dry_run=True (PADRÃO) só devolve preview — NADA vai pra Omie; confira com o
    operador e só então reenvie com dry_run=False."""
    return omie_write.alterar_conta_receber(
        cliente, codigo_lancamento_omie=codigo_lancamento_omie,
        valor_documento=valor_documento, data_vencimento=data_vencimento,
        data_previsao=data_previsao, codigo_categoria=codigo_categoria,
        codigo_cliente_fornecedor=codigo_cliente_fornecedor,
        id_conta_corrente=id_conta_corrente, numero_documento=numero_documento,
        observacao=observacao, codigo_tipo_documento=codigo_tipo_documento,
        omie_param_extra=omie_param_extra, dry_run=dry_run)


@mcp.tool()
def omie_excluir_conta_receber(cliente: str, codigo_lancamento_omie: int,
                               dry_run: bool = True) -> dict:
    """Exclui uma conta a RECEBER (por codigo_lancamento_omie). Irreversível na Omie.
    dry_run=True (PADRÃO) só devolve preview — NADA vai pra Omie; confira com o
    operador e só então reenvie com dry_run=False."""
    return omie_write.excluir_conta_receber(
        cliente, codigo_lancamento_omie=codigo_lancamento_omie, dry_run=dry_run)


@mcp.tool()
def omie_baixar_titulo(cliente: str, tipo: str, codigo_lancamento_omie: int,
                       valor: float | None = None, data: str | None = None,
                       id_conta_corrente: int | None = None, juros: float | None = None,
                       desconto: float | None = None, multa: float | None = None,
                       observacao: str | None = None, omie_endpoint: str | None = None,
                       omie_call: str | None = None, dry_run: bool = True) -> dict:
    """Baixa (liquida) um título no Omie. tipo = 'pagar' ou 'receber'. codigo_lancamento_omie
    = código do título; data yyyy-MM-dd; id_conta_corrente = conta da baixa. dry_run=True
    (PADRÃO) só devolve preview — NADA vai pra Omie; confira com o operador e só então
    reenvie com dry_run=False."""
    return omie_write.baixar_titulo(
        cliente, tipo=tipo, codigo_lancamento_omie=codigo_lancamento_omie,
        valor=valor, data=data, id_conta_corrente=id_conta_corrente,
        juros=juros, desconto=desconto, multa=multa, observacao=observacao,
        omie_endpoint=omie_endpoint, omie_call=omie_call, dry_run=dry_run)


@mcp.tool()
def omie_incluir_cliente_fornecedor(cliente: str, razao_social: str, cnpj_cpf: str,
                                    papel: str | None = None, nome_fantasia: str | None = None,
                                    email: str | None = None, pessoa_fisica: str | None = None,
                                    inativo: str | None = None, finops_id: str | None = None,
                                    dry_run: bool = True) -> dict:
    """Inclui (upsert) um cadastro de cliente/fornecedor no Omie. razao_social + cnpj_cpf
    obrigatórios; papel = 'cliente'|'fornecedor'|'ambos'; pessoa_fisica = 'S'|'N'.
    dry_run=True (PADRÃO) só devolve preview — NADA vai pra Omie; confira com o
    operador e só então reenvie com dry_run=False."""
    return omie_write.incluir_cliente_fornecedor(
        cliente, razao_social=razao_social, cnpj_cpf=cnpj_cpf, papel=papel,
        nome_fantasia=nome_fantasia, email=email, pessoa_fisica=pessoa_fisica,
        inativo=inativo, finops_id=finops_id, dry_run=dry_run)


@mcp.tool()
def omie_alterar_cliente_fornecedor(cliente: str, codigo_cliente_omie: int,
                                    razao_social: str | None = None, nome_fantasia: str | None = None,
                                    email: str | None = None, inativo: str | None = None,
                                    dry_run: bool = True) -> dict:
    """Altera um cadastro de cliente/fornecedor (por codigo_cliente_omie). Não há
    exclusão de cadastro — para desativar, passe inativo='S'. dry_run=True (PADRÃO)
    só devolve preview — NADA vai pra Omie; confira com o operador e só então reenvie
    com dry_run=False."""
    return omie_write.alterar_cliente_fornecedor(
        cliente, codigo_cliente_omie=codigo_cliente_omie, razao_social=razao_social,
        nome_fantasia=nome_fantasia, email=email, inativo=inativo, dry_run=dry_run)


def _selftest() -> int:
    """Checa o setup sem passar pelo Claude: caminhos resolvidos + carteira.
    Devolve 0 se conseguiu ler a carteira, 1 caso contrário."""
    print("── FullBPO-Omie · selftest ──")
    print(f"CONFIG_DIR (Drive)   : {config.CONFIG_DIR or '(não encontrado)'}")
    print(f"FULLBPO_HOME (local) : {config.FULLBPO_HOME}")
    print(f"FINOPS_URL           : {config.FINOPS_URL}")
    print(f"FINOPS_ANON_KEY      : {'ok' if config.FINOPS_ANON_KEY else 'AUSENTE'}")
    print(f"FINOPS_EMAIL         : {config.FINOPS_EMAIL or 'AUSENTE'}")
    print(f"FINOPS_PASSWORD      : {'ok' if config.FINOPS_PASSWORD else 'AUSENTE'}")
    print(f"FINOPS_EMPRESAS_FILE : {config.FINOPS_EMPRESAS_FILE}")

    pend = config.problemas_config()
    if pend:
        print("\nPendências de setup:")
        for p in pend:
            print(f"  - {p}")

    lista = finops_client.empresas()
    print(f"\nempresas() no mapa   : {len(lista)}")
    for e in lista[:5]:
        print(f"  · {e['nome']} → {e['company_id']}")
    if len(lista) > 5:
        print(f"  … (+{len(lista) - 5})")

    ok = bool(lista)
    print(f"\nresultado: {'OK' if ok else 'FALHOU (mapa de empresas vazio)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    mcp.run()
