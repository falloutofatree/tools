#!/usr/bin/env python3
"""
gsc-verify: verify a domain with Google via a Cloudflare DNS TXT record, then
add it as a Search Console domain property.

Steps per domain (each one is idempotent, so re-running is safe):
    1. Get the DNS_TXT token from the Site Verification API.
    2. Create the TXT record on the matching Cloudflare zone (skipped if present).
    3. Poll public resolvers (1.1.1.1 and 8.8.8.8, via DoH) until the record shows.
    4. Ask Google to verify (retried, since Google's resolvers can lag).
    5. Add sc-domain:<domain> to Search Console (skipped if already there).

Auth:
    Google: gcloud application-default credentials, or GOOGLE_ACCESS_TOKEN.
    Cloudflare: CLOUDFLARE_API_TOKEN (Zone:Read + DNS:Edit on the zone).

Usage:
    gsc_verify.py DOMAIN [DOMAIN ...] [--dry-run] [--timeout SECS] [--quota-project ID]

Examples:
    gsc_verify.py example.com
    gsc_verify.py example.com example.org --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


SV_API = "https://www.googleapis.com/siteVerification/v1"
SC_API = "https://www.googleapis.com/webmasters/v3"
CF_API = "https://api.cloudflare.com/client/v4"
DOH_RESOLVERS = {
    "1.1.1.1": "https://cloudflare-dns.com/dns-query",
    "8.8.8.8": "https://dns.google/resolve",
}
SCOPES = (
    "https://www.googleapis.com/auth/siteverification,"
    "https://www.googleapis.com/auth/webmasters,"
    "https://www.googleapis.com/auth/cloud-platform"
)
LOGIN_HINT = f"gcloud auth application-default login --scopes={SCOPES}"
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


class ApiError(Exception):
    pass


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def step(msg: str) -> None:
    print(f"  - {msg}", flush=True)


def normalize_domain(value: str) -> str:
    """Accept 'example.com', 'https://www.example.com/', 'sc-domain:example.com'."""
    v = value.strip().lower()
    v = re.sub(r"^sc-domain:", "", v)
    v = re.sub(r"^[a-z]+://", "", v).split("/")[0].rstrip(".")
    if not DOMAIN_RE.match(v):
        die(f"not a valid domain: {value!r}")
    return v


def http(method: str, url: str, headers: dict, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:800]
        raise ApiError(f"{method} {url} -> HTTP {e.code}: {detail}") from None
    except urllib.error.URLError as e:
        raise ApiError(f"{method} {url} -> {e.reason}") from None
    return json.loads(raw) if raw.strip() else {}


# --- Google -----------------------------------------------------------------

def adc_quota_project() -> str | None:
    """quota_project_id from the ADC file, if gcloud set one."""
    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.path.join(
        os.environ.get("CLOUDSDK_CONFIG", os.path.expanduser("~/.config/gcloud")),
        "application_default_credentials.json",
    )
    try:
        with open(path) as f:
            return json.load(f).get("quota_project_id")
    except (OSError, ValueError):
        return None


def google_headers(quota_project: str | None) -> dict:
    token = os.environ.get("GOOGLE_ACCESS_TOKEN", "").strip()
    if not token:
        try:
            token = subprocess.run(
                ["gcloud", "auth", "application-default", "print-access-token"],
                capture_output=True, text=True, check=True, timeout=60,
            ).stdout.strip()
        except FileNotFoundError:
            die("gcloud not found; install it or set GOOGLE_ACCESS_TOKEN.")
        except subprocess.CalledProcessError as e:
            die(f"could not get an ADC token ({e.stderr.strip()}).\nLog in with:\n  {LOGIN_HINT}")
    headers = {"Authorization": f"Bearer {token}"}
    # User ADC needs a quota project for these APIs, or Google returns 403.
    project = quota_project or os.environ.get("GOOGLE_CLOUD_QUOTA_PROJECT") or adc_quota_project()
    if project:
        headers["x-goog-user-project"] = project
    return headers


def sv_site(domain: str) -> dict:
    return {"type": "INET_DOMAIN", "identifier": domain}


def get_txt_token(g: dict, domain: str) -> str:
    resp = http("POST", f"{SV_API}/token", g,
                {"site": sv_site(domain), "verificationMethod": "DNS_TXT"})
    return resp["token"]


def is_verified(g: dict, domain: str) -> bool:
    resp = http("GET", f"{SV_API}/webResource", g)
    return any(r.get("site") == sv_site(domain) for r in resp.get("items", []))


def verify(g: dict, domain: str, attempts: int, delay: int) -> None:
    url = f"{SV_API}/webResource?verificationMethod=DNS_TXT"
    for i in range(1, attempts + 1):
        try:
            http("POST", url, g, {"site": sv_site(domain)})
            return
        except ApiError as e:
            if i == attempts:
                raise
            step(f"verify attempt {i}/{attempts} failed; retrying in {delay}s ({str(e)[:160]})")
            time.sleep(delay)


def sc_site_url(domain: str) -> str:
    return f"sc-domain:{domain}"


def in_search_console(g: dict, domain: str) -> bool:
    resp = http("GET", f"{SC_API}/sites", g)
    return any(s.get("siteUrl") == sc_site_url(domain) for s in resp.get("siteEntry", []))


def add_to_search_console(g: dict, domain: str) -> None:
    http("PUT", f"{SC_API}/sites/{urllib.parse.quote(sc_site_url(domain), safe='')}", g)


# --- Cloudflare -------------------------------------------------------------

def cf_headers() -> dict:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not token:
        die("missing env var CLOUDFLARE_API_TOKEN.")
    return {"Authorization": f"Bearer {token}"}


def find_zone(cf: dict, domain: str) -> tuple[str, str]:
    """Longest-suffix match, so sub.example.com finds the example.com zone."""
    labels = domain.split(".")
    for i in range(len(labels) - 1):
        name = ".".join(labels[i:])
        resp = http("GET", f"{CF_API}/zones?name={urllib.parse.quote(name)}", cf)
        if resp.get("result"):
            return resp["result"][0]["id"], name
    raise ApiError(f"no Cloudflare zone found for {domain} (check the token's Zone:Read scope)")


def unquote_txt(content: str) -> str:
    """Cloudflare may return TXT content quoted and split into 255-char chunks."""
    parts = re.findall(r'"((?:[^"\\]|\\.)*)"', content)
    return "".join(parts) if parts else content


def txt_record_exists(cf: dict, zone_id: str, domain: str, value: str) -> bool:
    q = urllib.parse.urlencode({"type": "TXT", "name": domain, "per_page": 100})
    resp = http("GET", f"{CF_API}/zones/{zone_id}/dns_records?{q}", cf)
    return any(unquote_txt(r.get("content", "")) == value for r in resp.get("result", []))


def create_txt_record(cf: dict, zone_id: str, domain: str, value: str) -> None:
    # Quoted content avoids Cloudflare's "TXT content should be quoted" warning.
    http("POST", f"{CF_API}/zones/{zone_id}/dns_records", cf, {
        "type": "TXT", "name": domain, "content": f'"{value}"', "ttl": 1,
        "comment": "Google Search Console domain verification (gsc-verify)",
    })


# --- DNS propagation --------------------------------------------------------

def doh_txt(endpoint: str, domain: str) -> list[str]:
    q = urllib.parse.urlencode({"name": domain, "type": "TXT"})
    resp = http("GET", f"{endpoint}?{q}", {"Accept": "application/dns-json"})
    return [unquote_txt(a.get("data", "")) for a in resp.get("Answer", []) if a.get("type") == 16]


def wait_for_txt(domain: str, value: str, timeout: int, interval: int) -> bool:
    deadline = time.monotonic() + timeout
    pending = dict(DOH_RESOLVERS)
    while True:
        for name, endpoint in list(pending.items()):
            try:
                if value in doh_txt(endpoint, domain):
                    step(f"TXT visible on {name}")
                    del pending[name]
            except ApiError:
                pass
        if not pending:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(interval)


# --- main -------------------------------------------------------------------

def run(domain: str, g: dict, cf: dict, args: argparse.Namespace) -> None:
    print(f"{domain}", flush=True)

    if is_verified(g, domain):
        step("already verified with Google; skipping DNS")
    else:
        value = get_txt_token(g, domain)
        step(f"token: {value}")
        zone_id, zone = find_zone(cf, domain)
        step(f"Cloudflare zone: {zone}")
        if txt_record_exists(cf, zone_id, domain, value):
            step("TXT record already present")
        elif args.dry_run:
            step("[dry-run] would create TXT record")
        else:
            create_txt_record(cf, zone_id, domain, value)
            step("TXT record created")
        if args.dry_run:
            step("[dry-run] would wait for DNS and verify")
        else:
            if not wait_for_txt(domain, value, args.timeout, args.interval):
                step(f"TXT not seen on all resolvers after {args.timeout}s; trying verify anyway")
            verify(g, domain, args.verify_attempts, args.interval)
            step("verified with Google")

    if in_search_console(g, domain):
        step(f"{sc_site_url(domain)} already in Search Console")
    elif args.dry_run:
        step(f"[dry-run] would add {sc_site_url(domain)} to Search Console")
    else:
        add_to_search_console(g, domain)
        step(f"added {sc_site_url(domain)} to Search Console")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify domains with Google via Cloudflare DNS and add them to Search Console.")
    parser.add_argument("domains", nargs="+", metavar="DOMAIN",
                        help="domain(s) to verify, e.g. example.com")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="read-only: show what would change without writing to Cloudflare or Google")
    parser.add_argument("-t", "--timeout", type=int, default=600,
                        help="seconds to wait for DNS propagation (default 600)")
    parser.add_argument("-i", "--interval", type=int, default=15,
                        help="seconds between DNS polls and verify retries (default 15)")
    parser.add_argument("--verify-attempts", type=int, default=8,
                        help="verify attempts before giving up (default 8)")
    parser.add_argument("--quota-project", metavar="ID",
                        help="GCP project billed for API quota (default: GOOGLE_CLOUD_QUOTA_PROJECT or ADC file)")
    args = parser.parse_args()

    domains = [normalize_domain(d) for d in args.domains]
    g = google_headers(args.quota_project)
    cf = cf_headers()

    failed = []
    for domain in domains:
        try:
            run(domain, g, cf, args)
        except ApiError as e:
            step(f"FAILED: {e}")
            failed.append(domain)
    if failed:
        die(f"{len(failed)} of {len(domains)} domain(s) failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
