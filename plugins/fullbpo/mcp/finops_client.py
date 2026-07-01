"""Ponte plugin → FinOps (engine Omie multi-tenant, na nuvem Supabase).

Fase 1 do blueprint Omie: o plugin PAROU de falar com o Omie direto. Agora ele
chama a Edge Function `mcp-server` do FinOps, que:
  1. valida o JWT do operador (este módulo cuida do login/refresh);
  2. confere se o operador pode ver aquele company_id (escopo por carteira);
  3. lê as chaves do Omie no Vault (server-side) e chama o Omie (read-only);
  4. devolve só o dado + grava auditoria.

Por isso as chaves do Omie NUNCA passam por aqui. O único segredo local é a
sessão do operador (refresh token), guardada em FINOPS_SESSION_FILE com chmod 600.

Auth = Supabase Auth (GoTrue), fluxo headless de senha:
  POST {url}/auth/v1/token?grant_type=password      {email, password}
  POST {url}/auth/v1/token?grant_type=refresh_token {refresh_token}
ambos com header apikey: <anon>. Devolvem {access_token, refresh_token,
expires_at, ...}. A Edge Function exige Authorization: Bearer <access_token>
e apikey: <anon>.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time

import httpx

import config

_TOKEN_PATH = "/auth/v1/token"
_MCP_PATH = "/functions/v1/mcp-server"
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

_session: dict | None = None
_lock = threading.Lock()


class FinOpsAuthError(RuntimeError):
    """Falha ao autenticar no FinOps (credenciais/refresh inválidos)."""


class FinOpsToolError(RuntimeError):
    """A Edge Function recusou a chamada ou a tool devolveu erro."""


# ─── Sessão em disco (refresh token = sensível, chmod 600) ───────────────────
def _load_session() -> dict | None:
    global _session
    if _session is not None:
        return _session
    try:
        with open(config.FINOPS_SESSION_FILE, encoding="utf-8") as f:
            _session = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _session = None
    return _session


def _save_session(data: dict) -> None:
    global _session
    _session = data
    path = config.FINOPS_SESSION_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


# ─── GoTrue (Supabase Auth) ──────────────────────────────────────────────────
def _post_token(grant: str, payload: dict) -> dict:
    if not config.FINOPS_ANON_KEY:
        raise FinOpsAuthError(
            "FINOPS_ANON_KEY ausente — falta o config.env na pasta FullBPO-MCP do "
            "Drive (ou o atalho da pasta não foi adicionado ao seu Drive).")
    url = f"{config.FINOPS_URL.rstrip('/')}{_TOKEN_PATH}?grant_type={grant}"
    with httpx.Client(timeout=30) as c:
        r = c.post(url, json=payload, headers={
            "apikey": config.FINOPS_ANON_KEY,
            "Content-Type": "application/json",
        })
    if r.status_code != 200:
        raise FinOpsAuthError(
            f"Auth FinOps falhou ({grant}): HTTP {r.status_code} {r.text[:200]}")
    return r.json()


def _password_grant() -> dict:
    if not config.FINOPS_EMAIL or not config.FINOPS_PASSWORD:
        raise FinOpsAuthError(
            "FINOPS_EMAIL/FINOPS_PASSWORD ausentes — crie ~/.fullbpo/credenciais.env "
            "com o seu login do FinOps e dê chmod 600.")
    data = _post_token("password", {
        "email": config.FINOPS_EMAIL,
        "password": config.FINOPS_PASSWORD,
    })
    _save_session(data)
    return data


def _refresh(refresh_token: str) -> dict:
    data = _post_token("refresh_token", {"refresh_token": refresh_token})
    _save_session(data)
    return data


def _access_token(force_refresh: bool = False) -> str:
    """Devolve um access_token válido, renovando/relogando conforme preciso."""
    with _lock:
        sess = _load_session()
        now = time.time()
        if not force_refresh and sess and sess.get("access_token"):
            if sess.get("expires_at", 0) > now + 60:
                return sess["access_token"]
        if sess and sess.get("refresh_token"):
            try:
                return _refresh(sess["refresh_token"])["access_token"]
            except FinOpsAuthError:
                pass  # refresh expirou → cai p/ login com senha
        return _password_grant()["access_token"]


# ─── Bridge p/ a Edge Function ───────────────────────────────────────────────
def call_tool(tool: str, params: dict | None = None) -> dict:
    """Chama uma tool do mcp-server do FinOps com o JWT do operador.

    Faz 1 retry com refresh/relogin se o 1º POST voltar 401 (token expirado).
    Devolve o `data` da tool; levanta FinOpsToolError em erro de tool/HTTP.
    """
    url = f"{config.FINOPS_URL.rstrip('/')}{_MCP_PATH}"
    body = {"tool": tool, "params": params or {}}

    def _do(token: str) -> httpx.Response:
        with httpx.Client(timeout=120) as c:
            return c.post(url, json=body, headers={
                "Authorization": f"Bearer {token}",
                "apikey": config.FINOPS_ANON_KEY,
                "Content-Type": "application/json",
            })

    r = _do(_access_token())
    if r.status_code == 401:
        r = _do(_access_token(force_refresh=True))

    if r.status_code != 200:
        raise FinOpsToolError(
            f"FinOps recusou '{tool}': HTTP {r.status_code} {r.text[:300]}")
    payload = r.json()
    if not payload.get("success", False):
        raise FinOpsToolError(f"Tool '{tool}' falhou: {payload.get('error') or payload}")
    return payload.get("data")


# ─── Mapa local nome→company_id (carteira do operador) ───────────────────────
def empresas() -> list[dict]:
    """Lista {nome, company_id} a partir de FINOPS_EMPRESAS_FILE (json local).

    O servidor não expõe a carteira; este mapa é o atalho amigável p/ chamar as
    tools por NOME em vez de decorar UUID. Aceita 2 formatos no arquivo:
      {"Cliente A": "uuid", ...}                  (dict simples)
      [{"nome": "...", "company_id": "..."}]      (lista de objetos)
    """
    try:
        with open(config.FINOPS_EMPRESAS_FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    if isinstance(raw, dict):
        return [{"nome": k, "company_id": v} for k, v in raw.items()]
    if isinstance(raw, list):
        return [
            {"nome": e.get("nome") or e.get("name"),
             "company_id": e.get("company_id") or e.get("id")}
            for e in raw if isinstance(e, dict)
        ]
    return []


def resolver_company_id(nome_ou_id: str) -> str:
    """Aceita um UUID (devolve direto) ou um nome (busca no mapa local).

    Match por nome: 1º exato (case-insensitive), depois por substring. Erra se
    não achar ou se houver ambiguidade — nunca chuta um company_id.
    """
    s = (nome_ou_id or "").strip()
    if not s:
        raise FinOpsToolError("Informe o nome do cliente ou o company_id.")
    if _UUID_RE.match(s):
        return s
    lista = empresas()
    alvo = s.lower()
    exatos = [e for e in lista if (e["nome"] or "").lower() == alvo]
    if exatos:
        return exatos[0]["company_id"]
    parciais = [e for e in lista if alvo in (e["nome"] or "").lower()]
    if not parciais:
        raise FinOpsToolError(
            f"Cliente {s!r} não encontrado em finops_empresas.json. "
            f"Use finops_empresas() p/ ver a lista, ou passe o company_id (UUID).")
    if len(parciais) > 1:
        nomes = ", ".join(m["nome"] for m in parciais)
        raise FinOpsToolError(
            f"{s!r} é ambíguo: {nomes}. Seja mais específico ou use o UUID.")
    return parciais[0]["company_id"]
