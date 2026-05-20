# tools

Personal Claude plugin marketplace and MCP servers.

## Plugins

- [`handoff`](handoff/) - write or update a terse handoff `.md` file capturing the current work, so it's easy to understand and pick up later.
- [`trello-board-peek`](trello-board-peek/) - peek at a Trello board: list its open cards grouped by list, optionally filtered.

## MCP servers

- [`xero-deep`](xero-deep/) - invoice-level and per-customer data from Xero. Complementary to the official Xero MCP connector at mcp.xero.com.

## Install

### Plugins

In Claude (Cowork or Claude Code), add this marketplace by GitHub URL, then install a plugin:

```bash
claude plugin marketplace add https://github.com/falloutofatree/tools.git
claude plugin install trello-board-peek@tools
```

### MCP servers

MCP servers are installed per-server, not via the marketplace. See each server's README for setup - e.g. [`xero-deep/README.md`](xero-deep/README.md) covers the Python venv install and the `claude mcp add` registration step.
