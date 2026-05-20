"""Async Xero API client: auth + tenant headers, pagination, 429 backoff."""

import asyncio

import httpx

API_BASE = "https://api.xero.com/api.xro/2.0"
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000
INVOICE_STATUSES = {"DRAFT", "SUBMITTED", "AUTHORISED", "PAID", "VOIDED", "DELETED"}


class XeroError(RuntimeError):
    def __init__(self, msg, status_code=None, retry_after_s=None):
        super().__init__(msg)
        self.status_code, self.retry_after_s = status_code, retry_after_s


def _esc(v): return v.replace('"', '""')


def _where_dates(df, dt):
    return "&&".join(p for p in (
        df and f"Date>=DateTime({df.year}, {df.month}, {df.day})",
        dt and f"Date<=DateTime({dt.year}, {dt.month}, {dt.day})",
    ) if p) or None


class XeroClient:
    def __init__(self, auth, http=None):
        self.auth, self.sem, self.own_http = auth, asyncio.Semaphore(5), http is None
        self.http = http or httpx.AsyncClient(timeout=30.0)

    async def close(self):
        if self.own_http:
            await self.http.aclose()
        await self.auth.close()

    async def _request(self, path, params=None, attempt=0):
        async with self.sem:
            tok, tid = await self.auth.access_token(), await self.auth.tenant_id()
            try:
                r = await self.http.get(
                    f"{API_BASE}{path}",
                    headers={"Authorization": f"Bearer {tok}",
                             "Xero-tenant-id": tid,
                             "Accept": "application/json"},
                    params=params)
            except httpx.TimeoutException as e:
                raise XeroError(f"timeout: {e}") from e
        if r.status_code == 401 and attempt == 0:
            await self.auth.access_token(force=True)
            return await self._request(path, params, attempt + 1)
        if r.status_code == 429:
            ra = float(r.headers.get("Retry-After") or 0) or None
            if attempt >= 5 or (ra and ra > 65):
                raise XeroError(f"rate limited; Retry-After={ra}s", 429, ra)
            await asyncio.sleep(ra or min(2 ** attempt, 30))
            return await self._request(path, params, attempt + 1)
        if r.status_code >= 400:
            if r.status_code >= 500 and attempt < 2:
                await asyncio.sleep(min(2 ** attempt, 5))
                return await self._request(path, params, attempt + 1)
            raise XeroError(f"HTTP {r.status_code} {r.text[:200]}", r.status_code)
        return r.json()

    async def _paginate(self, path, base, key, page, page_size):
        n = page if page is not None else 1
        while True:
            items = (await self._request(path, {**base, "page": n})).get(key) or []
            for x in items: yield x
            if page is not None or len(items) < page_size: return
            n += 1

    async def iter_invoices(self, *, contact_id=None, statuses=None, date_from=None,
                            date_to=None, page=None, page_size=DEFAULT_PAGE_SIZE):
        page_size = max(1, min(int(page_size), MAX_PAGE_SIZE))
        base = {"pageSize": page_size}
        if statuses:
            base["Statuses"] = ",".join(s.strip().upper() for s in statuses if s and s.strip())
        if contact_id:
            base["ContactIDs"] = contact_id
        if w := _where_dates(date_from, date_to):
            base["where"] = w
        async for inv in self._paginate("/Invoices", base, "Invoices", page, page_size):
            yield inv

    async def iter_contacts(self, *, name=None, email=None, include_archived=False,
                            all_contacts=False, page=None, page_size=DEFAULT_PAGE_SIZE):
        page_size = max(1, min(int(page_size), MAX_PAGE_SIZE))
        base = {"pageSize": page_size}
        wp = [s for s in ((not all_contacts) and "IsCustomer==true",
                          name and f'Name.Contains("{_esc(name)}")',
                          email and f'EmailAddress.Contains("{_esc(email)}")') if s]
        if wp:
            base["where"] = "&&".join(wp)
        if include_archived:
            base["includeArchived"] = "true"
        async for c in self._paginate("/Contacts", base, "Contacts", page, page_size):
            yield c
