"""xero-deep MCP server."""

import json
import sys
from decimal import Decimal

from mcp.server.fastmcp import FastMCP

from ._helpers import err, exc, parse_date, slim_customer, slim_invoice
from .auth import XeroAuth
from .xero_client import DEFAULT_PAGE_SIZE, INVOICE_STATUSES, XeroClient, XeroError

mcp = FastMCP("xero_deep_mcp")
_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True}
_client: XeroClient | None = None


async def _c():
    global _client
    if _client is None:
        _client = XeroClient(XeroAuth.from_env())
    return _client


@mcp.tool(name="get_invoices", annotations={"title": "Get Xero Invoices", **_RO})
async def get_invoices(customer_id: str | None = None, status: str | None = None,
                       date_from: str | None = None, date_to: str | None = None,
                       page: int | None = None, page_size: int = DEFAULT_PAGE_SIZE) -> str:
    """Filtered list of Xero invoices. customer_id=ContactID; status one of DRAFT/SUBMITTED/AUTHORISED/PAID/VOIDED/DELETED; dates YYYY-MM-DD; page 1-based (omit to merge all); page_size 1-1000."""
    try:
        s = status.strip().upper() if status else None
        if s and s not in INVOICE_STATUSES:
            return err(f"Invalid status {status!r}. Must be one of: {sorted(INVOICE_STATUSES)}")
        df, dt = parse_date(date_from, "date_from"), parse_date(date_to, "date_to")
        cli = await _c()
        invs = [slim_invoice(i) async for i in cli.iter_invoices(
            contact_id=customer_id, statuses=[s] if s else None,
            date_from=df, date_to=dt, page=page, page_size=page_size)]
    except (ValueError, XeroError, RuntimeError) as e:
        return exc(e)
    out = {"count": len(invs), "page": page, "page_size": page_size,
           "filters": {"customer_id": customer_id, "status": s,
                       "date_from": date_from, "date_to": date_to},
           "invoices": invs}
    if page is not None and len(invs) == page_size:
        out["note"] = f"Single page of {page_size}. Call with page+=1 for more."
    return json.dumps(out, indent=2, default=str)


@mcp.tool(name="get_customer_revenue",
          annotations={"title": "Get Customer Revenue (PAID invoices in timeframe)", **_RO})
async def get_customer_revenue(customer_id: str, date_from: str, date_to: str) -> str:
    """Sum PAID invoice Totals for one customer in a timeframe. Dates YYYY-MM-DD. Returns JSON."""
    try:
        df, dt = parse_date(date_from, "date_from"), parse_date(date_to, "date_to")
        cli = await _c()
        total, n = Decimal("0"), 0
        async for inv in cli.iter_invoices(contact_id=customer_id, statuses=["PAID"],
                                            date_from=df, date_to=dt):
            n += 1
            try:
                total += Decimal(str(inv.get("Total") or 0))
            except (ValueError, ArithmeticError):
                pass
    except (ValueError, XeroError, RuntimeError) as e:
        return exc(e)
    return json.dumps({"customer_id": customer_id, "date_from": date_from, "date_to": date_to,
                       "invoice_count": n, "total": f"{total:.2f}"}, indent=2)


@mcp.tool(name="get_customers",
          annotations={"title": "Get Xero Customers (search by name or email)", **_RO})
async def get_customers(name: str | None = None, email: str | None = None,
                        include_archived: bool = False, all_contacts: bool = False,
                        page: int | None = None,
                        page_size: int = DEFAULT_PAGE_SIZE) -> str:
    """Search customers by name and/or email (substring). Returns JSON. At least one filter required. By default only customers (IsCustomer=true); set all_contacts=true to include suppliers/vendors."""
    if not name and not email:
        return err("Provide at least one filter (name or email).")
    try:
        cli = await _c()
        custs = [slim_customer(x) async for x in cli.iter_contacts(
            name=name, email=email, include_archived=include_archived,
            all_contacts=all_contacts, page=page, page_size=page_size)]
    except (XeroError, RuntimeError) as e:
        return exc(e)
    return json.dumps({"count": len(custs), "page": page, "page_size": page_size,
                       "filters": {"name": name, "email": email,
                                   "include_archived": include_archived,
                                   "all_contacts": all_contacts},
                       "customers": custs}, indent=2, default=str)


def main():
    """--version prints version; otherwise starts the MCP server over stdio."""
    if sys.argv[1:2] in (["--version"], ["-v"]):
        from . import __version__
        print(f"xero-deep {__version__}")
        sys.exit(0)
    mcp.run()
