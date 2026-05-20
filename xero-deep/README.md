# xero-deep `v1.0.0 · 2026-05-20`

MCP server exposing invoice-level and per-customer data from Xero. Complementary to the [official Xero MCP connector](https://mcp.xero.com).

## What it does

Three read-only tools, naming follows the official connector's `get_*` convention:

- `get_invoices(customer_id?, status?, date_from?, date_to?, page?, page_size?)` - filterable invoice list. Dates are `YYYY-MM-DD`. `page_size` is `1-1000` (default `100`).
- `get_customer_revenue(customer_id, date_from, date_to)` - sum of `PAID` invoices for one customer in the timeframe.
- `get_customers(name?, email?, include_archived?, all_contacts?, page?, page_size?)` - search Xero Contacts and return `customer_id`, name, email, status. Filters AND together; at least one is required. Defaults to `IsCustomer=true` only; pass `all_contacts=true` to include suppliers/vendors.

`customer_id` maps to Xero's `ContactID`.

## Setup

### 1. Register a Xero app

- Visit https://developer.xero.com/app/manage and click `New app`.
- Name your app. Can't contain the word `Xero`.
- App type: `Web app`.
- Agree to requirements.
- OAuth 2.0 redirect URI: `http://localhost:5005/callback`.
- Note the `Client id` and generate a `Client secret`.

### 2. Install

Python 3.10+ required.

```bash
cd path/to/xero-deep
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Mint the initial refresh token

- Export the `Client id` and `Client secret` from step 1 as `XERO_CLIENT_ID` and `XERO_CLIENT_SECRET`.
- Run `xero-deep-init`.
- Open the URL it shows in a browser signed into Xero.
- Pick your organization and click `Allow access`.

Under the hood, `xero-deep-init`:

- Generates the PKCE verifier and challenge.
- Builds the Xero authorize URL and starts a local listener on `http://localhost:5005/callback`.
- Catches Xero's redirect after you approve consent and validates the OAuth `state` to prevent CSRF.
- Exchanges the authorization code for an access token + refresh token.
- Writes the token set atomically to `~/.xero-deep/tokens.json` (mode `0600`).

### 4. Persist env vars

Required:

```bash
export XERO_CLIENT_ID="..."
export XERO_CLIENT_SECRET="..."
```

Optional:

```bash
export XERO_REFRESH_TOKEN="..."        # fallback if ~/.xero-deep/tokens.json goes missing
export XERO_TENANT_ID="..."            # your specific Xero organization (set if you have more than one)
export XERO_TOKEN_STORE_PATH="..."     # override default ~/.xero-deep/tokens.json
```

Put these in `~/.zshenv` (macOS/Linux). Both Cowork and Claude Code read from the same place — Claude Code inherits your shell env directly, and xero-deep falls back to sourcing `~/.zshenv` itself when launched by a GUI app that doesn't pass shell env through. No need to duplicate secrets into any MCP client's config.

If you're on bash/fish or Windows, export them however your shell/OS prefers. The xero-deep binary will use them as long as they're in its process env at startup.

`XERO_TOKEN_STORE_PATH` is for cases where you want the token file somewhere other than `~/.xero-deep/tokens.json` - e.g. alongside the project (`./.xero_tokens.json`), a shared `/Users/Shared/` location, a directory backed up differently, or a per-environment path on a CI worker. Most setups never need to set it.

### 5. Smoke test

```bash
xero-deep-smoke
xero-deep-smoke --name "Acme"             # also exercises get_customers
```

The basic invocation walks a timeframe of recent paid invoices and totals one customer's revenue. To pin a specific customer with `--customer-id <ContactID>`, grab a `ContactID` from the JSON output of the previous run, or call `get_customers` (via Claude or `xero-deep-smoke --name`).

## Running

xero-deep runs as an MCP server over stdio - JSON-RPC messages on stdin/stdout, logs on stderr.

```bash
xero-deep
```

To stop the server in a terminal, press **Ctrl+D** (closes stdin, clean exit; Ctrl+C doesn't unblock the stdin reader on SIGINT).

### Register with Cowork

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```jsonc
{
  "mcpServers": {
    "xero-deep": {
      "command": "/absolute/path/to/.venv/bin/xero-deep",
      "args": []
    }
  }
}
```

Use the absolute path to the venv binary - GUI apps don't have your shell's `PATH`. No `env` block is needed; xero-deep sources `~/.zshenv` itself at startup when env vars aren't already in its process env. Quit and relaunch Cowork after editing.

### Register with Claude Code

```bash
claude mcp add xero-deep --scope user -- /absolute/path/to/.venv/bin/xero-deep
claude mcp list
```

Replace `/absolute/path/to/.venv/bin/xero-deep` with the absolute path to the installed entry point inside your venv. Easiest way to get it: with your venv activated, run `which xero-deep` and paste that path.

## What's cached

- **Refresh tokens**, in `~/.xero-deep/tokens.json` (mode 0600). Xero rotates the refresh token every time xero-deep exchanges it for a fresh access token, which happens whenever the cached access token is within 60 seconds of expiry (~30 min lifetime). The new value is written atomically (tmp + rename) so a crash mid-rotation can't leave a partial file. The exported `XERO_REFRESH_TOKEN` is only used to bootstrap the store if the file is missing.
- **Tenant ID**, in memory for the process lifetime. Resolved once via `/connections` on the first API call.

No invoice or customer data is cached. Every `get_*` call hits Xero.

## Rate limits

Xero allows:

- 60 calls per minute per tenant
- 5,000 calls per day per tenant
- 5 concurrent calls per tenant
- 10,000 calls per minute app-wide

The client caps in-flight requests at 5, honors `Retry-After` on every 429, and retries up to 5 times for waits under ~65s. Longer waits surface as a structured error with `retry_after_s`.

## Future ideas

- Basic caching of the customer directory.
- Initiating changes in Xero - create/update invoices, payments, customers.
