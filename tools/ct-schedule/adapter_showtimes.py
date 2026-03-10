#!/usr/bin/env python3
"""
ct-schedule/adapter_showtimes.py — Kinoteatr schedule adapter.

Extracts session times from movie pages.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

import requests
from bs4 import BeautifulSoup

TIME_RE = re.compile(r"(?<!\d)([01]\d|2[0-3]):([0-5]\d)(?!\d)")


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}


def to_datetime_iso(date_value: str, time_value: str) -> str:
    """Build local datetime for Naberezhnye Chelny (+03:00)."""
    return f"{date_value}T{time_value}:00+03:00"


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _extract_structured_showtimes(
    html: str,
    date_value: str,
    booking_url: str = "",
) -> list[dict[str, Any]]:
    """Extract showtimes from explicit seance blocks when available."""
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.select(".item.buy_seance")
    if not blocks:
        return []

    showtimes: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for block in blocks:
        time_node = block.select_one(".time")
        if time_node is None:
            continue

        match = TIME_RE.search(_clean_text(time_node.get_text(" ", strip=True)))
        if match is None:
            continue

        time_value = f"{match.group(1)}:{match.group(2)}"
        hall_node = block.select_one(".hall span") or block.select_one(".hall")
        price_node = block.select_one(".price")
        hall_value = _clean_text(hall_node.get_text(" ", strip=True)) if hall_node else ""
        price_value = _clean_text(price_node.get_text(" ", strip=True)) if price_node else ""
        dedupe_key = (time_value, hall_value, price_value)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        item: dict[str, Any] = {
            "time": time_value,
            "datetime_iso": to_datetime_iso(date_value, time_value),
        }
        if price_value:
            item["price"] = price_value
        if hall_value:
            item["hall"] = hall_value
        if booking_url:
            item["booking_url"] = booking_url
        showtimes.append(item)

    return showtimes


def parse_showtimes_html(html: str, date_value: str, booking_url: str = "") -> list[dict[str, Any]]:
    """Extract and normalize unique showtimes from HTML."""
    structured = _extract_structured_showtimes(html, date_value, booking_url=booking_url)
    if structured:
        return structured

    found = list(dict.fromkeys(
        f"{m.group(1)}:{m.group(2)}" for m in TIME_RE.finditer(html)
    ))

    showtimes: list[dict[str, Any]] = []
    for time_value in found:
        item: dict[str, Any] = {
            "time": time_value,
            "datetime_iso": to_datetime_iso(date_value, time_value),
        }
        if booking_url:
            item["booking_url"] = booking_url
        showtimes.append(item)

    return showtimes


def fetch_showtimes(movie_url: str, date_value: str, timeout: int = 20) -> list[dict[str, Any]]:
    """Fetch movie page and parse showtimes."""
    try:
        response = requests.get(movie_url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectionError(f"Failed to fetch schedule from {movie_url}: {exc}") from exc

    return parse_showtimes_html(response.text, date_value, booking_url=movie_url)


def dry_run_showtimes(movie_id: str, date_value: str) -> list[dict[str, Any]]:
    """Generate deterministic mock showtimes for dry-run mode."""
    slots = ["10:10", "12:40", "15:20", "17:50", "20:30", "22:55"]
    digest = hashlib.sha1(f"{movie_id}|{date_value}".encode("utf-8")).hexdigest()
    seed = int(digest[:8], 16)

    first_idx = seed % len(slots)
    second_idx = (first_idx + 2 + (seed % 3)) % len(slots)
    values = sorted({slots[first_idx], slots[second_idx]})

    return [{"time": v, "datetime_iso": to_datetime_iso(date_value, v)} for v in values]
