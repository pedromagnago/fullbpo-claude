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
    """Falha estruturada, sem descartar a causa nem induzir repetição de escrita."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.details = details or {'error': message, 'estado': 'falha', 'proximo_passo': 'Confira a mensagem e consulte o contexto; não presuma falta de ferramenta.'}



# ─── Sessão em disco (refresh token = sensível, chmod 600) ───────────────────
def _load_session() -> dict | None:
    global _session
    if _session is not None:
        return _session
    try:
        with open(config.FINOPS_SESSION_FILE, encoding="utf-8") as f:
            _session = json.load(f)
        # Uma troca de login local nunca reutiliza a sessão de outra pessoa.
        email = (_session.get('user') or {}).get('email', '')
        if config.FINOPS_EMAIL and email.casefold() != config.FINOPS_EMAIL.casefold():
            _session = None
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
def request(body: dict) -> dict:
    """POST autenticado. Preserva pending, token, source e o recibo de execução.

    Só repete após 401, nunca após timeout/5xx de escrita com resultado desconhecido.
    """
    url = f"{config.FINOPS_URL.rstrip('/')}{_MCP_PATH}"

    def _do(token: str) -> httpx.Response:
        with httpx.Client(timeout=120) as c:
            return c.post(url, json=body, headers={
                "Authorization": f"Bearer {token}",
                "apikey": config.FINOPS_ANON_KEY,
                "Content-Type": "application/json",
            })

    try:
        r = _do(_access_token())
        if r.status_code == 401:
            r = _do(_access_token(force_refresh=True))
    except httpx.TransportError as error:
        raise FinOpsToolError('Conexão interrompida; resultado não confirmado.', {
            'error': 'transport_error', 'estado': 'resultado_desconhecido',
            'proximo_passo': 'Não repita escrita. Consulte o registro para saber se a operação ocorreu. Para consulta de leitura, tente novamente.',
        }) from error

    if r.status_code != 200:
        try:
            problem = r.json()
        except ValueError:
            problem = {}
        if not isinstance(problem, dict):
            problem = {}
        code = problem.get('error', 'http_error')
        next_step = {
            401: 'Sessão inválida. Confira o login individual no setup; não peça senha no chat.',
            403: 'Acesso negado. Consulte finops_contexto e confira empresa, ação e papel. Isso não significa ausência da ferramenta. Implantação operacional usa finops_implantacao.',
            400: 'Confira os parâmetros, a versão e as inconsistências retornadas; consulte novamente antes de alterar.',
            429: 'Limite temporário de chamadas; aguarde antes de nova consulta.',
        }.get(r.status_code, 'Consulte o estado do registro antes de repetir uma escrita; encaminhe o request_id ao suporte.')
        details = {k: problem[k] for k in ('error', 'request_id', 'dica', 'campo', 'schema', 'exemplo_de_chamada') if k in problem}
        details.update({'http_status': r.status_code, 'estado': 'resultado_desconhecido' if r.status_code >= 500 else 'recusado', 'proximo_passo': next_step})
        raise FinOpsToolError(f'FinOps: HTTP {r.status_code} {code}', details)
    payload = r.json()
    if not payload.get("success", False):
        raise FinOpsToolError(f"FinOps: {payload.get('error') or payload}")
    return payload


def call_tool(tool: str, params: dict | None = None) -> dict:
    """Compatibilidade dos atalhos Omie, sem perder uma pendência de aprovação."""
    payload = request({"tool": tool, "params": params or {}})
    return payload if payload.get('pending') or 'data' not in payload else payload['data']


def catalogo() -> list[dict]:
    return request({'op': 'listar_tools'})['tools']


# ─── Mapa local nome→company_id (carteira do operador) ───────────────────────
def empresas() -> list[dict]:
    """Carteira atual e autorizada do servidor. Não cai no arquivo antigo em erro."""
    result = []
    offset = 0
    for _ in range(1000):
        page = call_tool('listar_empresas', {'offset': offset, 'limit': 100})
        if not isinstance(page, dict) or not isinstance(page.get('empresas'), list):
            raise FinOpsToolError('Resposta de carteira inválida; não use o mapa local como confirmação.')
        result.extend(page['empresas'])
        following = page.get('next_offset')
        if following is None:
            return result
        if not isinstance(following, int) or following <= offset:
            raise FinOpsToolError('Paginação de carteira inválida; consulta incompleta.')
        offset = following
    raise FinOpsToolError('Carteira excedeu o limite de páginas; consulta incompleta.')


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
    exatos = [e for e in lista if alvo in [(e.get(k) or '').lower() for k in ('nome', 'nome_fantasia')]]
    if len(exatos) == 1:
        return exatos[0]["company_id"]
    parciais = exatos or [e for e in lista if any(alvo in (e.get(k) or '').lower() for k in ('nome', 'nome_fantasia'))]
    if not parciais:
        raise FinOpsToolError(
            f"Cliente {s!r} não encontrado na carteira atual deste login. "
            f"Confira nome/razão social e comercial_onboarding; ausência na carteira não prova que não há proposta ou contrato.")
    if len(parciais) > 1:
        nomes = ", ".join(m["nome"] for m in parciais)
        raise FinOpsToolError(
            f"{s!r} é ambíguo: {nomes}. Seja mais específico ou use o UUID.")
    return parciais[0]["company_id"]
