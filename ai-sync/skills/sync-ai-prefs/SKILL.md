---
name: sync-ai-prefs
description: Check the AI User Preferences gist for a version bump and, if newer, replace the AI client's account-wide instructions (Claude, ChatGPT, or another compatible client) with the gist content.
---

# Sync AI Prefs

1. Fetch gist.github.com/falloutofatree/7adeb626d774a4590c476dde9904f7ea
2. Check the version of the account-wide instructions already in your context. If the gist is not newer, stop.
3. In the browser, update the setting for your client and save:
   - Claude: textarea called "Instructions for Claude" at claude.ai/new#settings/account
   - ChatGPT: Settings > Personalization > Custom instructions
4. If the setting's name or location differed from step 3, propose an update to this skill
