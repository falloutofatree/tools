"""One-shot bootstrap for the initial Xero refresh token. See README step 3."""

import base64
import hashlib
import http.server
import secrets
import sys
import threading
import time
import urllib.parse

import httpx

from .auth import XERO_TOKEN_URL, basic_auth, save_tokens
from .config import Settings

REDIRECT_URI = "http://localhost:5005/callback"
SCOPES = ("offline_access accounting.invoices.read "
          "accounting.contacts.read accounting.settings.read")


def _pkce():
    v = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode()
    c = base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).rstrip(b"=").decode()
    return v, c


def _consent_url(cid, challenge, state):
    return "https://login.xero.com/identity/connect/authorize?" + urllib.parse.urlencode({
        "response_type": "code", "client_id": cid, "redirect_uri": REDIRECT_URI,
        "scope": SCOPES, "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
    })


def _wait_for_redirect():
    """Bind localhost:5005, wait for /callback, return its query params."""
    captured, done = {}, threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" in qs or "error" in qs:
                captured.update({k: (qs.get(k) or [None])[0]
                                 for k in ("code", "state", "error", "error_description")})
                done.set()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Captured. You can close this tab.")
        def log_message(self, *_): pass

    srv = http.server.HTTPServer(("127.0.0.1", 5005), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        done.wait(timeout=600)
    finally:
        srv.shutdown()
    return captured


def _exchange(cid, cs, code, verifier):
    r = httpx.post(
        XERO_TOKEN_URL,
        data={"grant_type": "authorization_code", "code": code,
              "redirect_uri": REDIRECT_URI, "code_verifier": verifier, "client_id": cid},
        headers={"Authorization": basic_auth(cid, cs),
                 "Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0)
    if r.status_code != 200: sys.exit(f"Exchange failed: {r.status_code} {r.text}")
    return r.json()


def main():
    try:
        s = Settings.from_env()
    except RuntimeError as e:
        sys.exit(str(e))

    verifier, challenge = _pkce()
    state = secrets.token_urlsafe(16)
    print(f"\nOpen this URL in a browser signed into Xero, approve consent:\n\n"
          f"{_consent_url(s.client_id, challenge, state)}\n")

    if not (cap := _wait_for_redirect()):
        sys.exit("Timed out (10 min).")
    if cap.get("error"):
        sys.exit(f"Xero error: {cap['error']} - {cap.get('error_description')}")
    if cap.get("state") != state:
        sys.exit("OAuth state mismatch.")
    if not (code := cap.get("code")):
        sys.exit("No code returned.")

    d = _exchange(s.client_id, s.client_secret, code, verifier)
    save_tokens(s.token_store_path, {
        "access_token": d["access_token"],
        "refresh_token": d["refresh_token"],
        "expires_at": time.time() + float(d.get("expires_in", 1800)),
    })
    print(f"\nDone. Token saved to {s.token_store_path}.")
    print(f'\nOptional bootstrap fallback:\n  export XERO_REFRESH_TOKEN="{d["refresh_token"]}"')
