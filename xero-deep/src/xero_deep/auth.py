"""Xero OAuth: refresh access tokens, rotate refresh tokens, resolve tenant."""

import asyncio
import base64
import json
import os
import time
from pathlib import Path

import httpx

from .config import Settings

XERO_TOKEN_URL = "https://identity.xero.com/connect/token"
CONNECTIONS_URL = "https://api.xero.com/connections"
TIMEOUT_S = 30.0


def basic_auth(cid: str, cs: str) -> str:
    return "Basic " + base64.b64encode(f"{cid}:{cs}".encode()).decode()


def save_tokens(path: Path, tokens: dict) -> None:
    """Atomic write to the token store, 0600 perms."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(tokens, indent=2))
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    tmp.replace(path)


class XeroAuth:
    @classmethod
    def from_env(cls) -> "XeroAuth":
        return cls(Settings.from_env())

    def __init__(self, settings: Settings):
        self.s = settings
        self._tenant_id = settings.tenant_id
        self._lock = asyncio.Lock()
        self._http = httpx.AsyncClient(timeout=TIMEOUT_S)
        # Load tokens from disk; fall back to the env-var bootstrap.
        p = settings.token_store_path
        try:
            self.tokens = json.loads(p.read_text()) if p.exists() else None
        except (OSError, ValueError):
            self.tokens = None
        if self.tokens is None:
            if not settings.refresh_token:
                raise RuntimeError("No refresh token; run xero-deep-init.")
            self.tokens = {"refresh_token": settings.refresh_token,
                           "access_token": "", "expires_at": 0}

    async def close(self):
        await self._http.aclose()

    async def _refresh(self):
        r = await self._http.post(
            XERO_TOKEN_URL,
            data={"grant_type": "refresh_token",
                  "refresh_token": self.tokens["refresh_token"]},
            headers={"Authorization": basic_auth(self.s.client_id, self.s.client_secret),
                     "Content-Type": "application/x-www-form-urlencoded"})
        if r.status_code != 200:
            raise RuntimeError(f"Refresh failed: HTTP {r.status_code} {r.text[:200]}")
        d = r.json()
        self.tokens = {"access_token": d["access_token"],
                       "refresh_token": d["refresh_token"],
                       "expires_at": time.time() + float(d.get("expires_in", 1800))}
        save_tokens(self.s.token_store_path, self.tokens)

    async def access_token(self, force: bool = False) -> str:
        async with self._lock:
            if force or self.tokens.get("expires_at", 0) - 60 < time.time():
                await self._refresh()
            return self.tokens["access_token"]

    async def tenant_id(self) -> str:
        if self._tenant_id:
            return self._tenant_id
        r = await self._http.get(
            CONNECTIONS_URL,
            headers={"Authorization": f"Bearer {await self.access_token()}",
                     "Accept": "application/json"})
        if r.status_code != 200:
            raise RuntimeError(f"Tenants lookup failed: HTTP {r.status_code}")
        conns = r.json()
        if not conns:
            raise RuntimeError("No Xero tenants connected; re-run xero-deep-init.")
        self._tenant_id = conns[0]["tenantId"]
        return self._tenant_id
