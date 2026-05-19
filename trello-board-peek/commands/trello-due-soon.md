---
description: Show Trello cards on the default board due within N days (default 7), with overdue items at the top
argument-hint: [days]
---

Run this on the user's local shell (Desktop Commander or equivalent host-execution tool), NOT the workspace sandbox. The script needs the user's shell env (`TRELLO_API_KEY`, `TRELLO_TOKEN`) and network access to `api.trello.com`. Show the output verbatim.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/list_cards.py" --due-within $ARGUMENTS
```
