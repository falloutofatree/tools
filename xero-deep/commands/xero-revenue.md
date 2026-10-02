---
description: Get total revenue (PAID invoices) for a Xero customer in a date range
argument-hint: <customer-id|name|email> <date_from YYYY-MM-DD> <date_to YYYY-MM-DD>
---

Call `mcp__xero-deep__get_customer_revenue` with arguments parsed from: $ARGUMENTS

Parsing rules:
- If first token is a UUID, use directly as `customer_id`
- If first token contains `@`, call `mcp__xero-deep__get_customers` with it as `email` to resolve the ContactID
- Otherwise treat as a name and call `mcp__xero-deep__get_customers` with it as `name` to resolve the ContactID
- If lookup returns multiple matches, list them and ask the user to clarify before proceeding
- Remaining tokens are `date_from` and `date_to` (YYYY-MM-DD)

Display: customer name/ID, date range, invoice count, and total revenue.
