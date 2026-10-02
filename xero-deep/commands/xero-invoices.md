---
description: List Xero invoices, optionally filtered by customer, status, or date range
argument-hint: [status] [date_from YYYY-MM-DD] [date_to YYYY-MM-DD]
---

Call `mcp__xero-deep__get_invoices` with filters parsed from: $ARGUMENTS

Parsing rules:
- A status keyword (DRAFT, SUBMITTED, AUTHORISED, PAID, VOIDED, DELETED) -> `status`
- A UUID -> `customer_id`
- First date -> `date_from`, second date -> `date_to`
- No arguments -> fetch all with defaults

Display results as a table: Invoice #, Customer, Date, Due Date, Status, Amount. Show total count and any active filters.
