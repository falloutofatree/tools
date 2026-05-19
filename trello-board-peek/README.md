# trello-board-peek `v1.0.0 · 2026-05-18`

Peek at a Trello board: list its open cards grouped by list, optionally filtered by one list or by due date. Read-only, no caching.

## What it does

Adds three slash commands:

- `/trello [board-url]` - full board view; defaults to your `TRELLO_DEFAULT_BOARD` if no URL given.
- `/trello-list <name>` - peek at one list (case-insensitive substring match).
- `/trello-due-soon [days]` - cards due within N days (default 7), with overdue items in a banner at the top.

Also bundles a `trello-board-peek` skill for natural-language discovery ("what's on my Trello board?").

## Credentials

Reads `TRELLO_API_KEY`, `TRELLO_TOKEN`, and (optional) `TRELLO_DEFAULT_BOARD` from `os.environ`. Set them in your shell init — `~/.zshenv` is sourced by non-interactive shells, which is what slash command bash invocations run as:

```bash
export TRELLO_API_KEY="..."
export TRELLO_TOKEN="..."
export TRELLO_DEFAULT_BOARD="https://trello.com/b/yourshortlink"  # optional
```

Then `source ~/.zshenv` or open a new terminal.

Get the API key and token from a Power-Up at https://trello.com/power-ups/admin.

## Script reference

Source: `scripts/list_cards.py`. Run it directly with `--help` for the full flag list.

Common invocations:

```bash
# Default board, all lists
python3 scripts/list_cards.py

# Explicit board (overrides TRELLO_DEFAULT_BOARD)
python3 scripts/list_cards.py "https://trello.com/b/NfmI6req"

# One list (case-insensitive substring match)
python3 scripts/list_cards.py --list "Critical Path"

# Cards due within N days, overdue items in a banner at top
python3 scripts/list_cards.py --due-within 7

# --due-within alone defaults to 7
python3 scripts/list_cards.py --due-within

# Combine: due-soon items on a single list
python3 scripts/list_cards.py --list "This week" --due-within 14
```

Key behaviors:

- Plain text output, grouped by list, with per-section card counts. Cards show due dates and labels when present.
- `--json` returns the board as JSON instead of formatted text. It honors `--list` and `--due-within`; when `--due-within` is set, overdue cards are pulled into a separate `overdue` key.
- Read-only; never mutates the board.
- Archived/closed lists and cards are excluded.
- One API call per invocation. Trello rate limits: 300 req/10s per key, 100 req/10s per token.
