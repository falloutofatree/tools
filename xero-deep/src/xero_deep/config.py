"""Environment-driven configuration.

Required env vars:
    XERO_CLIENT_ID, XERO_CLIENT_SECRET
Optional env vars:
    XERO_REFRESH_TOKEN     - bootstrap if the token store is missing
    XERO_TENANT_ID         - pin a specific Xero organization
    XERO_TOKEN_STORE_PATH  - default: ~/.xero-deep/tokens.json
"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


def _maybe_load_zsh_env():
    """Source ~/.zshenv into os.environ if required vars are missing.

    Lets GUI MCP clients (which don't inherit shell env) launch this binary
    directly without an `env` block in their config.
    """
    if os.environ.get("XERO_CLIENT_ID") and os.environ.get("XERO_CLIENT_SECRET"):
        return
    if not (Path.home() / ".zshenv").exists():
        return
    try:
        out = subprocess.run(
            ["/bin/zsh", "-c", "source ~/.zshenv && env"],
            capture_output=True, text=True, timeout=5, check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            if k.startswith("XERO_") and k not in os.environ:
                os.environ[k] = v


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    refresh_token: str
    tenant_id: str | None
    token_store_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        _maybe_load_zsh_env()
        cid = os.environ.get("XERO_CLIENT_ID", "").strip()
        cs = os.environ.get("XERO_CLIENT_SECRET", "").strip()
        if not (cid and cs):
            missing = [k for k, v in [("XERO_CLIENT_ID", cid),
                                       ("XERO_CLIENT_SECRET", cs)] if not v]
            raise RuntimeError(
                f"Missing required env vars: {', '.join(missing)}. See README.")
        default_store = os.path.join(os.path.expanduser("~"), ".xero-deep", "tokens.json")
        return cls(
            client_id=cid,
            client_secret=cs,
            refresh_token=os.environ.get("XERO_REFRESH_TOKEN", "").strip(),
            tenant_id=os.environ.get("XERO_TENANT_ID", "").strip() or None,
            token_store_path=Path(
                os.environ.get("XERO_TOKEN_STORE_PATH", default_store)
            ).expanduser(),
        )
