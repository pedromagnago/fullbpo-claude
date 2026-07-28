# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2.0,<2", "httpx>=0.28", "python-dotenv>=1.0"]
# ///
"""Servidor MCP D4Sign do plugin FullBPO — gestão de contratos (assinatura eletrônica).

Server SEPARADO do Omie (fullbpo-omie) de propósito: se faltar credencial D4Sign,
o Omie/FinOps continua de pé. Leitura livre; escrita com dry_run=True por PADRÃO
(devolve preview). `d4sign_enviar_para_assinatura` dispara e-mail ao cliente —
só executa com dry_run=False explícito.

Segredo: tokenAPI/cryptKey vêm de ~/.fullbpo/credenciais.env (nunca no repo). O
dir deste script entra no sys.path[0], então `import d4sign` é o irmão em mcp/.

Uso:
  uv run --script d4sign_mcp.py             → sobe o servidor MCP (stdio)
  uv run --script d4sign_mcp.py --selftest  → testa a conexão e sai (sem Claude)
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

import d4sign

mcp = FastMCP("fullbpo-d4sign")


# ─── Leitura ─────────────────────────────────────────────────────────────────
@mcp.tool()
def d4sign_status() -> dict:
    """Sanidade da conexão D4Sign (credencial + amostra de cofres). Rode primeiro."""
    return d4sign.status()


@mcp.tool()
def d4sign_listar_cofres() -> dict:
    """Cofres (safes) da conta D4Sign. Use pra achar o uuid_cofre ao criar documento."""
    return {"cofres": d4sign.listar_cofres()}


@mcp.tool()
def d4sign_listar_documentos(pagina: int = 1) -> dict:
    """Lista documentos do D4Sign (até 500/página). Traz uuid, nome e status de cada."""
    return {"pagina": pagina, "documentos": d4sign.listar_documentos(pagina)}


@mcp.tool()
def d4sign_documento(uuid: str) -> dict:
    """Status + signatários de UM documento (uuid). Pra conferir andamento da assinatura."""
    return {"documento": d4sign.documento(uuid)}


@mcp.tool()
def d4sign_baixar_documento(uuid: str, tipo: str = "PDF") -> dict:
    """Gera link temporário de download do documento (tipo PDF|ZIP). Não baixa o binário."""
    return d4sign.baixar_documento(uuid, tipo=tipo)


# ─── Escrita (dry_run=True por padrão → preview) ─────────────────────────────
@mcp.tool()
def d4sign_criar_documento(uuid_cofre: str, caminho_arquivo: str,
                          uuid_pasta: str | None = None, dry_run: bool = True) -> dict:
    """Sobe um contrato (arquivo local) pra um cofre D4Sign. dry_run=True só previsualiza."""
    return d4sign.criar_documento(uuid_cofre, caminho_arquivo,
                                 uuid_pasta=uuid_pasta, dry_run=dry_run)


@mcp.tool()
def d4sign_definir_signatarios(uuid: str, signatarios: list[dict],
                              dry_run: bool = True) -> dict:
    """Registra signatários. signatarios=[{email, act:'1', foreign:'0'}]. dry_run=True previsualiza."""
    return d4sign.definir_signatarios(uuid, signatarios, dry_run=dry_run)


@mcp.tool()
def d4sign_enviar_para_assinatura(uuid: str, mensagem: str | None = None,
                                 pular_email: bool = False, dry_run: bool = True) -> dict:
    """⚠️ DISPARA e-mail de assinatura ao cliente. dry_run=True só previsualiza;
    use dry_run=False pra enviar de verdade."""
    return d4sign.enviar_para_assinatura(uuid, mensagem=mensagem,
                                        pular_email=pular_email, dry_run=dry_run)


@mcp.tool()
def d4sign_cancelar_documento(uuid: str, comentario: str | None = None,
                             dry_run: bool = True) -> dict:
    """Cancela um documento no D4Sign (status → Cancelado). dry_run=True só previsualiza."""
    return d4sign.cancelar_documento(uuid, comentario=comentario, dry_run=dry_run)


def _selftest() -> int:
    """Testa a conexão real (GET /safes) sem passar pelo Claude."""
    import json
    print("── FullBPO-D4Sign · selftest ──")
    st = d4sign.status()
    # não imprime token/crypt (status() já devolve só 'ok'/'AUSENTE')
    print(json.dumps(st, ensure_ascii=False, indent=2)[:1800])
    ok = st.get("conexao") == "ok"
    print(f"\nresultado: {'OK' if ok else 'sem conexão — confira a credencial'}")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    mcp.run()
