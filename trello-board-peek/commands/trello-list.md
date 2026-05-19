---
description: Show one list on the default Trello board (case-insensitive substring match)
argument-hint: <list-name>
---

Run this on the user's local shell (Desktop Commander or equivalent host-execution tool), NOT the workspace sandbox. The script needs the user's shell env (`TRELLO_API_KEY`, `TRELLO_TOKEN`) and network access to `api.trello.com`. Show the output verbatim.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/list_cards.py" --list "$ARGUMENTS"
```
