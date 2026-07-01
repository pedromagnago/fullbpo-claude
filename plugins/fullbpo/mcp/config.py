"""Config slim do pacote Omie/FinOps do plugin FullBPO.

Diferente do server/config.py do projeto local (servidor completo): aqui só vivem
as variáveis FINOPS_*, e a config é DESCOBERTA em duas camadas:

  1. Config COMUM (não-secreta) numa pasta compartilhada do Google Drive:
       FullBPO-MCP/config.env          → FINOPS_URL + FINOPS_ANON_KEY
       FullBPO-MCP/finops_empresas.json → mapa mestre nome→company_id
     A pasta só sincroniza no disco se o membro clicar "Adicionar atalho ao
     Drive" (senão fica em "Compartilhados comigo", que o Drive Desktop não
     baixa). Override manual: env FULLBPO_DRIVE_DIR apontando pra pasta.

  2. IDENTIDADE individual (sensível), local por máquina, fora do Drive/repo:
       ~/.fullbpo/credenciais.env       → FINOPS_EMAIL + FINOPS_PASSWORD (chmod 600)
       ~/.fullbpo/.finops_session.json  → refresh token em cache (chmod 600, auto)

Nenhum segredo real mora no repositório do plugin: a anon é publicável e o mapa
nome→UUID não concede acesso (o gate por carteira decide no servidor do FinOps).
"""
from __future__ import annotations

import glob
import os
from pathlib import Path

from dotenv import load_dotenv


def _discover_config_dir() -> Path | None:
    """Acha a pasta FullBPO-MCP: 1º o override FULLBPO_DRIVE_DIR, depois globs
    rasos (sem **) sobre os pontos de sync do Google Drive for Desktop."""
    override = os.environ.get("FULLBPO_DRIVE_DIR")
    if override and Path(override).is_dir():
        return Path(override)
    home = Path.home()
    pats = [
        "Library/CloudStorage/GoogleDrive-*/Meu Drive/FullBPO-MCP",
        "Library/CloudStorage/GoogleDrive-*/My Drive/FullBPO-MCP",
        "Library/CloudStorage/GoogleDrive-*/Meu Drive/*/FullBPO-MCP",
        "Library/CloudStorage/GoogleDrive-*/My Drive/*/FullBPO-MCP",
        "Library/CloudStorage/GoogleDrive-*/Meu Drive/*/*/FullBPO-MCP",
        "Library/CloudStorage/GoogleDrive-*/My Drive/*/*/FullBPO-MCP",
    ]
    for p in pats:
        for hit in sorted(glob.glob(str(home / p))):
            if Path(hit).is_dir():
                return Path(hit)
    return None


CONFIG_DIR = _discover_config_dir()
if CONFIG_DIR:
    load_dotenv(CONFIG_DIR / "config.env")

FULLBPO_HOME = Path(os.environ.get("FULLBPO_HOME", Path.home() / ".fullbpo"))
FULLBPO_HOME.mkdir(parents=True, exist_ok=True)
load_dotenv(FULLBPO_HOME / "credenciais.env", override=True)


def env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


FINOPS_URL = env("FINOPS_URL", "https://rlznohwlgcfjbbgnwozf.supabase.co")
FINOPS_ANON_KEY = env("FINOPS_ANON_KEY", "")
FINOPS_EMAIL = env("FINOPS_EMAIL", "")
FINOPS_PASSWORD = env("FINOPS_PASSWORD", "")
FINOPS_SESSION_FILE = FULLBPO_HOME / ".finops_session.json"
FINOPS_EMPRESAS_FILE = (
    (CONFIG_DIR / "finops_empresas.json") if CONFIG_DIR
    else (FULLBPO_HOME / "finops_empresas.json")
)


def problemas_config() -> list[str]:
    """Lista pendências de setup em linguagem de onboarding (vazio = tudo ok)."""
    out = []
    if not CONFIG_DIR:
        out.append(
            "pasta FullBPO-MCP do Drive não encontrada — abra a pasta compartilhada "
            "e clique 'Adicionar atalho ao Drive', ou defina FULLBPO_DRIVE_DIR.")
    elif not FINOPS_ANON_KEY:
        out.append(f"FINOPS_ANON_KEY ausente em {CONFIG_DIR / 'config.env'}.")
    if not (FINOPS_EMAIL and FINOPS_PASSWORD):
        out.append(
            f"login ausente — crie {FULLBPO_HOME / 'credenciais.env'} com "
            "FINOPS_EMAIL e FINOPS_PASSWORD (seu login do FinOps) e dê chmod 600.")
    return out
