# gsc-domain-verify `v0.3.0 · 2026-10-29`

Verify a domain in Google Search Console via the Site Verification API and a DNS TXT record. Built for agents: API steps use prefilled API Explorer URLs with machine-readable results; only sign-ins and Google's consent popup need a human.

## Skills

- `gsc-domain-verify`: get a DNS_TXT token, add it at the domain root, confirm propagation, verify via the API, then confirm the `sc-domain:` property in Search Console.

## Install

```bash
claude plugin marketplace add https://github.com/falloutofatree/tools.git
claude plugin install gsc-domain-verify@tools
```
