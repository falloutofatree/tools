---
description: Search Xero customers by name or email
argument-hint: <name-or-email>
---

Call `mcp__xero-deep__get_customers` with the argument from: $ARGUMENTS

Parsing rules:
- If argument contains `@`, pass as `email`
- Otherwise pass as `name`

Display results as a compact list: ContactID, Name, Email. Show total count.
