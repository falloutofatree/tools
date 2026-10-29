# gsc-verify `v1.0.0 · 2026-10-29`

Verify a domain with Google via a Cloudflare DNS TXT record, then add it as a Search Console domain property (`sc-domain:example.com`). Idempotent: every step checks current state first, so re-running is safe.

## What it does

Adds a `/gsc-verify <domain> [domain ...] [--dry-run]` slash command, plus a `gsc-verify` skill for natural-language requests ("add example.com to Search Console").

Per domain:

1. Skips straight to step 5 if Google already lists the domain as verified.
2. Gets the `DNS_TXT` token from the Site Verification API.
3. Finds the Cloudflare zone (longest-suffix match, so subdomains work) and creates the TXT record unless it already exists.
4. Polls 1.1.1.1 and 8.8.8.8 over DNS-over-HTTPS until the record shows (no `dig` needed), then asks Google to verify, retrying because Google's resolvers can lag.
5. Adds `sc-domain:<domain>` to Search Console unless already there.

The TXT record is left in place on purpose: Google re-checks it periodically, and removing it eventually drops verification.

## Setup

### Google

1. Pick a GCP project to bill API quota to, and enable both APIs on it:

   ```bash
   gcloud services enable siteverification.googleapis.com searchconsole.googleapis.com --project=PROJECT_ID
   ```

2. Log in with the needed scopes (`cloud-platform` is required for gcloud ADC):

   ```bash
   gcloud auth application-default login --scopes=https://www.googleapis.com/auth/siteverification,https://www.googleapis.com/auth/webmasters,https://www.googleapis.com/auth/cloud-platform
   ```

3. Set the quota project. User ADC without one gets `403 ... requires a quota project`:

   ```bash
   gcloud auth application-default set-quota-project PROJECT_ID
   ```

The script reads the quota project from the ADC file; override with `--quota-project` or `GOOGLE_CLOUD_QUOTA_PROJECT`. To skip gcloud entirely, set `GOOGLE_ACCESS_TOKEN` to a token carrying the same scopes.

The Google account you log in with becomes the verified owner of the domain.

### Cloudflare

Create an API token at https://dash.cloudflare.com/profile/api-tokens with `Zone:Read` and `DNS:Edit`, scoped to the zones you want, and export it (e.g. in `~/.zshenv`, which non-interactive shells source):

```bash
export CLOUDFLARE_API_TOKEN="..."
```

## Script reference

Source: `scripts/gsc_verify.py` (stdlib only). Run with `--help` for all flags.

```bash
# Preview: reads Google and Cloudflare, writes nothing
python3 scripts/gsc_verify.py example.com --dry-run

# Live run, several domains
python3 scripts/gsc_verify.py example.com example.org

# Slow DNS: wait up to 30 min, poll every 30s
python3 scripts/gsc_verify.py example.com --timeout 1800 --interval 30
```

Key behaviors:

- Accepts `example.com`, `https://www.example.com/` (host is used as-is) or `sc-domain:example.com`.
- Domains run in sequence; a failure on one is reported and the rest continue. Exit code is non-zero if any failed.
- If DNS hasn't shown on both resolvers by `--timeout`, it still attempts verification (`--verify-attempts`, default 8, spaced by `--interval`).
- The Google token is fetched once per run (valid about an hour), so very long batches may need splitting.
