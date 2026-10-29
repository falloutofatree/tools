---
description: Verify domain(s) with Google via Cloudflare DNS and add them to Search Console
argument-hint: <domain> [domain ...] [--dry-run]
---

Run this on the user's local shell (Desktop Commander or equivalent host-execution tool), NOT the workspace sandbox. The script needs the user's gcloud application-default credentials, `CLOUDFLARE_API_TOKEN`, and network access to `googleapis.com` and `api.cloudflare.com`. It writes a DNS record and a Search Console property, so if the user has not clearly asked for a live run, run with `--dry-run` first and confirm. Show the output verbatim.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gsc_verify.py" $ARGUMENTS
```
