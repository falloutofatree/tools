"""Shared helpers for server.py: JSON shapes, date parsing, slim projections."""

import json
import re
from datetime import date, datetime, timezone

from .xero_client import XeroError

_DATE_RE = re.compile(r"^/Date\((-?\d+)")
_INV_F = ("InvoiceID", "InvoiceNumber", "Type", "Status", "SubTotal", "TotalTax",
          "Total", "AmountDue", "AmountPaid", "AmountCredited", "Reference")
_INV_D = ("Date", "DueDate", "FullyPaidOnDate", "UpdatedDateUTC")
_CUST_F = ("Name", "EmailAddress", "ContactStatus")


def iso(v):
    if not v:
        return None
    if m := _DATE_RE.match(v):
        try:
            return datetime.fromtimestamp(int(m.group(1)) / 1000,
                                          tz=timezone.utc).date().isoformat()
        except (ValueError, OverflowError):
            return v
    return v[:10] if len(v) >= 10 else v


def slim_invoice(r):
    c = r.get("Contact") or {}
    return {**{k: r.get(k) for k in _INV_F}, **{k: iso(r.get(k)) for k in _INV_D},
            "Customer": {"ContactID": c.get("ContactID"), "Name": c.get("Name")}}


def slim_customer(r):
    return {"customer_id": r.get("ContactID"), **{k: r.get(k) for k in _CUST_F}}


def err(msg, **extra):
    return json.dumps({"error": msg, **extra}, indent=2)


def exc(e):
    if isinstance(e, XeroError):
        d = {k: v for k, v in (("status_code", e.status_code),
                               ("retry_after_s", e.retry_after_s)) if v}
        return err(str(e), **d)
    return err(str(e))


def parse_date(v, name):
    if v is None:
        return None
    try:
        return date.fromisoformat(v)
    except ValueError as e:
        raise ValueError(f"{name} must be YYYY-MM-DD, got {v!r}") from e
