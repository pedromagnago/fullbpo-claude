"""D4Sign — assinatura eletrônica de contratos (conta única FullBPO).

Cliente REST fino sobre a API v1 do D4Sign. Diferente do Omie (multi-tenant via
FinOps), o D4Sign é SINGLE-TENANT: uma conta FullBPO que envia contratos aos
clientes. As credenciais (tokenAPI + cryptKey) são um par único, lidas de
~/.fullbpo/credenciais.env (chmod 600, fora do git) — nenhum segredo mora no repo.

Auth: a API exige tokenAPI + cryptKey como query em TODA chamada. Nunca ecoamos
esses valores em preview/erro (o preview mostra a rota sem os params de auth).

Escrita segue o padrão da casa (omie_write): dry_run=True por PADRÃO. Sem
dry_run=False explícito, a função só devolve o PREVIEW (método + rota + payload),
sem tocar no D4Sign. `enviar_para_assinatura` dispara e-mail ao cliente — a mesma
trava vale, com aviso reforçado.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

# Identidade sensível, local por máquina (mesma pasta do FinOps), fora do git.
FULLBPO_HOME = Path(os.environ.get("FULLBPO_HOME", Path.home() / ".fullbpo"))
load_dotenv(FULLBPO_HOME / "credenciais.env", override=True)

TOKEN_API = os.environ.get("D4SIGN_TOKEN_API", "")
CRYPT_KEY = os.environ.get("D4SIGN_CRYPT_KEY", "")
BASE_URL = os.environ.get(
    "D4SIGN_BASE_URL", "https://secure.d4sign.com.br/api/v1"
).rstrip("/")
TIMEOUT = float(os.environ.get("D4SIGN_TIMEOUT", "30"))


class D4SignError(RuntimeError):
    """Erro de configuração, rede ou resposta da API D4Sign."""


def _auth_params() -> dict:
    if not (TOKEN_API and CRYPT_KEY):
        raise D4SignError(
            "Credenciais D4Sign ausentes. Adicione D4SIGN_TOKEN_API e "
            "D4SIGN_CRYPT_KEY em ~/.fullbpo/credenciais.env (chmod 600). "
            "Veja mcp/credenciais.env.example."
        )
    return {"tokenAPI": TOKEN_API, "cryptKey": CRYPT_KEY}


def _url(path: str) -> str:
    return f"{BASE_URL}/{path.lstrip('/')}"


def _request(method: str, path: str, *, params: dict | None = None,
             json: Any = None, files: Any = None, data: dict | None = None) -> Any:
    """Chamada autenticada. Injeta tokenAPI+cryptKey na query; nunca os expõe em erro."""
    q = dict(_auth_params())
    if params:
        q.update({k: v for k, v in params.items() if v is not None})
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.request(method, _url(path), params=q, json=json,
                                  files=files, data=data)
    except httpx.HTTPError as exc:
        raise D4SignError(f"Falha de rede em {method} {path}: {exc}") from exc
    if resp.status_code >= 400:
        # o corpo do D4Sign costuma trazer {"message": ...}; recorta pra não poluir
        raise D4SignError(f"D4Sign HTTP {resp.status_code} em {method} {path}: "
                          f"{resp.text[:400]}")
    try:
        return resp.json()
    except ValueError:
        return {"raw": resp.text}


def _limpar(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def _preview(method: str, path: str, payload: dict) -> dict:
    """Preview de escrita — sem auth, sem tocar na API (dry_run)."""
    return {
        "dry_run": True,
        "acao": f"{method} {path}",
        "payload": payload,
        "obs": "Confira e reenvie com dry_run=False para executar de fato.",
    }


def _signer(s: dict) -> dict:
    """Normaliza um signatário. act='1' assina; foreign='0' = doc BR (CPF)."""
    if not s.get("email"):
        raise D4SignError(f"Signatário sem 'email': {s}")
    out = {
        "email": s["email"],
        "act": str(s.get("act", "1")),
        "foreign": str(s.get("foreign", "0")),
    }
    # campos opcionais aceitos pela API, repassados só se vierem
    for k in ("display_name", "documentation", "birthday", "certificadoicpbr",
              "assinatura_presencial", "docauth", "docauthandselfie",
              "whatsapp", "phone_number", "password_code", "auth_pix", "embed_methodauth"):
        if s.get(k) is not None:
            out[k] = s[k]
    return out


# ─── LEITURA ─────────────────────────────────────────────────────────────────
def listar_cofres() -> Any:
    """GET /safes — cofres (safes) da conta. Necessário pra achar o uuid_cofre."""
    return _request("GET", "/safes")


def listar_documentos(pagina: int = 1) -> Any:
    """GET /documents — até 500 documentos por página (param pg)."""
    return _request("GET", "/documents", params={"pg": pagina})


def documento(uuid: str) -> Any:
    """GET /documents/{uuid} — status, nome, páginas, cofre e signatários."""
    return _request("GET", f"/documents/{uuid}")


def baixar_documento(uuid: str, tipo: str = "PDF", idioma: str = "pt") -> Any:
    """POST /documents/{uuid}/download — devolve URL temporária (não o binário)."""
    return _request("POST", f"/documents/{uuid}/download",
                   json={"type": tipo, "language": idioma})


# ─── ESCRITA (dry_run=True por padrão) ───────────────────────────────────────
def criar_documento(uuid_cofre: str, caminho_arquivo: str,
                    uuid_pasta: str | None = None, dry_run: bool = True) -> Any:
    """POST /documents/{uuid_cofre}/upload — sobe um arquivo local pro cofre."""
    arq = Path(caminho_arquivo).expanduser()
    if not arq.is_file():
        raise D4SignError(f"Arquivo não encontrado: {arq}")
    payload = _limpar({"uuid_safe": uuid_cofre, "arquivo": arq.name,
                       "uuid_folder": uuid_pasta})
    if dry_run:
        return _preview("POST", f"/documents/{uuid_cofre}/upload", payload)
    data = _limpar({"uuid_folder": uuid_pasta})
    with arq.open("rb") as fh:
        files = {"file": (arq.name, fh)}
        return _request("POST", f"/documents/{uuid_cofre}/upload",
                       files=files, data=data or None)


def definir_signatarios(uuid: str, signatarios: list[dict],
                       dry_run: bool = True) -> Any:
    """POST /documents/{uuid}/createlist — registra a lista de signatários.

    Cada signatário: {email, act:'1'(assinar), foreign:'0'(BR), ...}.
    """
    signers = [_signer(s) for s in signatarios]
    payload = {"signers": signers}
    if dry_run:
        return _preview("POST", f"/documents/{uuid}/createlist", payload)
    return _request("POST", f"/documents/{uuid}/createlist", json=payload)


def enviar_para_assinatura(uuid: str, mensagem: str | None = None,
                          pular_email: bool = False, dry_run: bool = True) -> Any:
    """POST /documents/{uuid}/sendtosigner — ⚠️ DISPARA e-mail de assinatura ao cliente."""
    payload = _limpar({
        "message": mensagem,
        "skip_email": "1" if pular_email else None,
        "workflow": "0",
    })
    if dry_run:
        prev = _preview("POST", f"/documents/{uuid}/sendtosigner", payload)
        prev["aviso"] = "AÇÃO EXTERNA: com dry_run=False, envia e-mail de assinatura ao cliente."
        return prev
    return _request("POST", f"/documents/{uuid}/sendtosigner", json=payload)


def cancelar_documento(uuid: str, comentario: str | None = None,
                      dry_run: bool = True) -> Any:
    """POST /documents/{uuid}/cancel — cancela o documento (status → Cancelado)."""
    payload = _limpar({"comment": comentario})
    if dry_run:
        return _preview("POST", f"/documents/{uuid}/cancel", payload)
    return _request("POST", f"/documents/{uuid}/cancel", json=payload)


# ─── Sanidade ────────────────────────────────────────────────────────────────
def status() -> dict:
    """Diagnóstico: credencial presente? base? Se houver credencial, testa GET /safes."""
    info = {
        "base_url": BASE_URL,
        "token_api": "ok" if TOKEN_API else "AUSENTE",
        "crypt_key": "ok" if CRYPT_KEY else "AUSENTE",
        "credenciais_env": str(FULLBPO_HOME / "credenciais.env"),
    }
    if not (TOKEN_API and CRYPT_KEY):
        info["conexao"] = "sem credencial"
        return info
    try:
        cofres = listar_cofres()
        info["conexao"] = "ok"
        # amostra enxuta pra não despejar tudo
        if isinstance(cofres, list):
            info["qtd_cofres"] = len(cofres)
            info["amostra_cofres"] = cofres[:5]
        else:
            info["amostra_cofres"] = cofres
    except D4SignError as exc:
        info["conexao"] = f"falhou: {exc}"
    return info
