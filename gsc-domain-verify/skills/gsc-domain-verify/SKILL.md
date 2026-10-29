---
name: gsc-domain-verify
description: Verify a domain in Google Search Console via the Site Verification API and a DNS TXT record. Use when asked to verify a domain in Search Console. Requires browser interaction.
---

# Google Search Console Domain Verification

`v0.1.0 · 2026-10-29`

This skill is built for agents: API steps use prefilled URLs with machine-readable results; only the sign-ins and Google's consent popup require browser interaction. If you're working by hand, Search Console's Add property option is about as quick.

**Replace `example.com` with your domain throughout.**

1. **Sign In:** From a browser, sign in to search.google.com/search-console. In another tab, sign into the domain's DNS host.

2. **Get Token:** In a third tab, open the URL below, open the API panel, and click Execute. Approve Google's consent popup (or have the account owner do so). The popup may open behind the window; no response appears until it's approved. Copy the full token, including `google-site-verification=`.

   `https://developers.google.com/site-verification/v1/webResource/getToken?apix=true&apix_params={"resource":{"verificationMethod":"DNS_TXT","site":{"type":"INET_DOMAIN","identifier":"example.com"}}}`

3. **Add DNS Record:** Add a TXT record at the domain root (`@` or blank) with the token as its value and the default TTL. Some hosts need the value in double quotes. Don't change other records.

4. **Confirm Propagation:** Wait until the token appears in `dig +short TXT example.com @<nameserver>` (find it with `dig +short NS example.com`) or a web DNS checker.

5. **Verify:** Open the URL below and click Execute, approving the popup again if needed. Expect a 200 listing the owners.

   `https://developers.google.com/site-verification/v1/webResource/insert?apix=true&apix_params={"verificationMethod":"DNS_TXT","resource":{"site":{"type":"INET_DOMAIN","identifier":"example.com"}}}`

6. **Search Console:** Open `https://search.google.com/search-console?resource_id=sc-domain:example.com`, click "Verify your ownership" (it should auto-verify), and confirm the Overview page loads.
