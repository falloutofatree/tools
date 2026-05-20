"""Read-only smoke test for xero-deep."""

import argparse
import asyncio
import json
import sys
from datetime import date, timedelta

from .server import get_customer_revenue, get_customers, get_invoices


async def _run(df, dt, cid, name):
    print(f"Timeframe: {df} -> {dt}\n")

    p = json.loads(await get_invoices(customer_id=cid, status="PAID",
                                       date_from=df, date_to=dt))
    if "error" in p:
        sys.exit(f"FAIL get_invoices: {p['error']}")
    invs = p["invoices"]
    print(f"[1] {len(invs)} invoices")

    target = cid or (invs[0]["Customer"]["ContactID"] if invs else None)
    if target:
        p = json.loads(await get_customer_revenue(customer_id=target,
                                                   date_from=df, date_to=dt))
        if "error" in p:
            sys.exit(f"FAIL get_customer_revenue: {p['error']}")
        print(f"[2] invoice_count={p['invoice_count']}, total={p['total']}")

    if name:
        p = json.loads(await get_customers(name=name))
        if "error" in p:
            sys.exit(f"FAIL get_customers: {p['error']}")
        print(f"[3] {p['count']} customers")
    print("OK")


def main():
    t = date.today()
    a = argparse.ArgumentParser(prog="xero-deep-smoke")
    a.add_argument("--date-from", default=(t - timedelta(days=365 * 3)).isoformat())
    a.add_argument("--date-to", default=t.isoformat())
    a.add_argument("--customer-id")
    a.add_argument("--name")
    args = a.parse_args()
    asyncio.run(_run(args.date_from, args.date_to, args.customer_id, args.name))
