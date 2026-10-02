---
name: trello-board-peek
description: Triggers when the user asks for Trello board content in natural language - e.g. "what's on my Trello board", "what cards are in the Backlog list", "what's due soon". For the direct slash commands /trello, /trello-list, /trello-due-soon, the command bodies invoke the script directly and this skill is not consulted.
---

# Trello Board Peek

Run the script at `${CLAUDE_PLUGIN_ROOT}/scripts/list_cards.py` with flags appropriate to the user's intent. See `README.md` in the plugin root for the canonical flag and output reference, or invoke the script with `--help`.

**Tooling**: invoke on the user's local shell (Desktop Commander or equivalent host-execution tool), NOT the workspace sandbox. The script reads `TRELLO_API_KEY` / `TRELLO_TOKEN` from the user's shell environment and makes outbound HTTPS calls to `api.trello.com`, both of which are typically unavailable inside the workspace sandbox.

Show the output verbatim. No summarizing or commentary unless the user asks.
