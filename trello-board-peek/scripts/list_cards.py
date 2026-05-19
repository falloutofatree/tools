#!/usr/bin/env python3
"""
trello-board-peek: list open cards on a Trello board, grouped by list.

Reads TRELLO_API_KEY, TRELLO_TOKEN, and (optionally) TRELLO_DEFAULT_BOARD from
the environment.

Usage:
    list_cards.py [BOARD] [--list NAME] [--due-within DAYS] [--json]

Examples:
    list_cards.py                                  # uses TRELLO_DEFAULT_BOARD
    list_cards.py https://trello.com/b/a1BPiyZO    # explicit override
    list_cards.py --list "Critical Path"           # default board, one list
    list_cards.py --due-within 7                   # cards due in next week
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


API_BASE = "https://api.trello.com/1"
SHORT_LINK_RE = re.compile(r"(?:trello\.com/b/)?([A-Za-z0-9_-]{6,})")


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def resolve_board(cli_value: str | None) -> str:
    """Pick the board: explicit CLI arg wins, else TRELLO_DEFAULT_BOARD."""
    if cli_value:
        return cli_value
    env = os.environ.get("TRELLO_DEFAULT_BOARD", "").strip()
    if env:
        return env
    die("no board specified and TRELLO_DEFAULT_BOARD is not set.")


def parse_short_link(value: str) -> str:
    """Extract the board short link from a URL or pass through a bare one.
    Trims trailing slug/extension like 'NfmI6req.json' or 'NfmI6req/slug'."""
    value = value.strip()
    if not value:
        die("empty board identifier")
    m = SHORT_LINK_RE.search(value)
    if not m:
        die(f"can't parse short link from: {value!r}")
    return m.group(1).split("/", 1)[0].split(".", 1)[0]


def get_credentials() -> tuple[str, str]:
    key = os.environ.get("TRELLO_API_KEY", "").strip()
    token = os.environ.get("TRELLO_TOKEN", "").strip()
    missing = [n for n, v in (("TRELLO_API_KEY", key), ("TRELLO_TOKEN", token)) if not v]
    if missing:
        die(f"missing env var(s): {', '.join(missing)}.")
    return key, token


def fetch_board(short_link: str, key: str, token: str) -> dict:
    """One call: board metadata + open lists + open cards on each list."""
    params = {
        "lists": "open",
        "list_fields": "name,pos",
        "cards": "open",
        "card_fields": "name,idList,due,shortUrl,labels",
        "fields": "name,shortUrl",
        "key": key,
        "token": token,
    }
    url = f"{API_BASE}/boards/{short_link}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        if e.code == 401:
            die("401 Unauthorized: check TRELLO_API_KEY/TRELLO_TOKEN and board access.")
        if e.code == 404:
            die(f"404: board '{short_link}' not found or inaccessible.")
        die(f"API error {e.code}: {body}")
    except urllib.error.URLError as e:
        die(f"network error: {e.reason}")


def parse_due(card: dict) -> dt.datetime | None:
    """Trello returns due dates as ISO 8601 strings. None if no due set."""
    raw = card.get("due")
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def format_card_line(card: dict) -> str:
    bits = [f"- {card['name']}"]
    if card.get("due"):
        bits.append(f"(due {card['due'][:10]})")
    labels = [lbl.get("name") for lbl in card.get("labels", []) if lbl.get("name")]
    if labels:
        bits.append(f"[{', '.join(labels)}]")
    return " ".join(bits)


def filter_board(
    board: dict,
    list_filter: str | None,
    due_within_days: int | None,
) -> dict:
    """Apply --list and --due-within, returning a board dict with filtered
    `lists` and `cards`. When due_within_days is set, past-due cards are
    pulled out under an `overdue` key so text and JSON output share one view."""
    raw_lists = sorted(board.get("lists", []), key=lambda l: l.get("pos", 0))
    if list_filter:
        needle = list_filter.lower()
        lists = [l for l in raw_lists if needle in l["name"].lower()]
        if not lists:
            die(f"no list matches '{list_filter}'.")
    else:
        lists = raw_lists

    kept_list_ids = {l["id"] for l in lists}
    cards = [c for c in board.get("cards", []) if c["idList"] in kept_list_ids]

    if due_within_days is None:
        return {**board, "lists": lists, "cards": cards}

    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now + dt.timedelta(days=due_within_days)
    within: list[dict] = []
    overdue: list[dict] = []
    for c in cards:
        due = parse_due(c)
        if due is None:
            continue
        if due < now:
            overdue.append(c)
        elif due <= cutoff:
            within.append(c)
    overdue.sort(key=lambda c: c.get("due") or "")
    return {**board, "lists": lists, "cards": within, "overdue": overdue}


def format_text(board: dict, due_within_days: int | None) -> str:
    lines: list[str] = []
    lists = board.get("lists", [])
    cards_by_list: dict[str, list[dict]] = {}
    for c in board.get("cards", []):
        cards_by_list.setdefault(c["idList"], []).append(c)
    overdue = board.get("overdue", [])

    board_name = board.get("name", "(unnamed board)")
    short_url = board.get("shortUrl", "")
    visible_total = sum(len(cards_by_list.get(l["id"], [])) for l in lists)
    if due_within_days is not None:
        summary = f"{plural(len(lists), 'list')}, {plural(visible_total, 'card')} due within {due_within_days}d"
    else:
        summary = f"{plural(len(lists), 'list')}, {plural(visible_total, 'open card')}"
    header = f"Board: {board_name}"
    if short_url:
        header += f" ({short_url})"
    lines.append(f"{header} - {summary}")
    lines.append("")

    if overdue:
        lines.append(f"!! OVERDUE ({len(overdue)}) !!")
        for c in overdue:
            lines.append(format_card_line(c))
        lines.append("")

    # When filtering by due date, hide empty lists so the output stays focused.
    hide_empty = due_within_days is not None
    rendered_any = False
    for lst in lists:
        bucket = cards_by_list.get(lst["id"], [])
        if hide_empty and not bucket:
            continue
        rendered_any = True
        lines.append(f"== {lst['name']} ({len(bucket)}) ==")
        if not bucket:
            lines.append("(empty)")
        else:
            for c in bucket:
                lines.append(format_card_line(c))
        lines.append("")

    if hide_empty and not rendered_any and not overdue:
        lines.append(f"(no cards due within {due_within_days}d and nothing overdue)")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="List open cards on a Trello board, grouped by list.")
    parser.add_argument("board", nargs="?", default=None,
                        help="Board URL or short link. Falls back to TRELLO_DEFAULT_BOARD.")
    parser.add_argument("-l", "--list", dest="list_filter", metavar="NAME",
                        help="Filter to lists whose name contains NAME (case-insensitive).")
    parser.add_argument("-d", "--due-within", dest="due_within", type=int, nargs="?", const=7,
                        default=None, metavar="DAYS",
                        help="Cards due within DAYS (default 7 if no value). Overdue in a banner at top.")
    parser.add_argument("-j", "--json", action="store_true",
                        help="Emit JSON instead of formatted text. Honors --list and --due-within; "
                             "when --due-within is set, overdue cards are returned under an 'overdue' key.")
    args = parser.parse_args()

    if args.due_within is not None and args.due_within < 0:
        die("--due-within must be a non-negative integer.")

    short_link = parse_short_link(resolve_board(args.board))
    key, token = get_credentials()
    board = fetch_board(short_link, key, token)
    filtered = filter_board(board, args.list_filter, args.due_within)

    if args.json:
        json.dump(filtered, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(format_text(filtered, args.due_within))


if __name__ == "__main__":
    main()
