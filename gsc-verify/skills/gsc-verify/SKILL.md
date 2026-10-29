---
name: gsc-verify
description: Triggers when the user asks in natural language to verify a domain with Google, add a domain to Google Search Console, or set up Search Console via Cloudflare DNS - e.g. "verify example.com in Search Console", "add my domain to GSC". For the direct /gsc-verify slash command, the command body invokes the script directly and this skill is not consulted.
---

# GSC Verify

Run the script at `${CLAUDE_PLUGIN_ROOT}/scripts/gsc_verify.py` with the domain(s) the user named. See `README.md` in the plugin root for setup, flags and behavior, or invoke the script with `--help`.

**Tooling**: invoke on the user's local shell (Desktop Commander or equivalent host-execution tool), NOT the workspace sandbox. The script needs the user's gcloud application-default credentials and `CLOUDFLARE_API_TOKEN`, and makes outbound HTTPS calls to Google and Cloudflare.

**Writes**: the script creates a Cloudflare TXT record and a Search Console property. Unless the user clearly asked for a live run, run with `--dry-run` first, show the output, and confirm before the live run.

If it fails with a token or 403 error, point the user to the Setup section of the README (login scopes, quota project, enabled APIs). Show the output verbatim.
