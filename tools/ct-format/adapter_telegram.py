#!/usr/bin/env python3
"""
ct-format/adapter_telegram.py — Telegram Markdown Renderer (вилка)

Renders filtered movies as Telegram markdown message.
Pure function: data in → markdown out.
"""

from datetime import datetime
from typing import Optional


def render_message(
    filtered: list,
    city_display: str,
    date: Optional[str] = None
) -> str:
    """Render filtered movies as Telegram markdown with Today and Coming Week sections."""
    if not date:
        date = datetime.now().strftime("%d.%m.%Y")

    today_str = datetime.now().strftime("%Y-%m-%d")

    # Split movies into playing today vs playing later in the week
    # Use available_days_accurate as source of truth for actual play dates
    playing_today = []
    playing_later = []

    for item in filtered:
        movie = item.get("movie", {})
        showtimes = movie.get("showtimes", [])

        # Prefer accurate days from data-dates attribute (source of truth)
        accurate_days = movie.get("available_days_accurate", [])
        available_days = movie.get("available_days", [])
        all_days = accurate_days if accurate_days else available_days

        if accurate_days:
            # Use accurate dates to determine if playing today
            if today_str in accurate_days:
                playing_today.append(item)
            else:
                # Movie plays on future dates only
                playing_later.append(item)
        elif showtimes:
            # Fallback: use showtimes as indicator for today
            playing_today.append(item)
        elif available_days:
            if today_str in available_days:
                playing_today.append(item)
            elif any(d != today_str for d in available_days):
                playing_later.append(item)
        else:
            # Backward-compatible fallback for minimal filtered payloads
            playing_today.append(item)

    lines = [
        f"📅 {date}",
        "",
        "┏━━ СЕГОДНЯ ━━┓",
        ""
    ]

    must_see_today = [m for m in playing_today if m.get("recommendation") == "must_see"]
    recommended_today = [m for m in playing_today if m.get("recommendation") == "recommended"]

    if must_see_today:
        lines.extend(["🌟 ОБЯЗАТЕЛЬНО", ""])
        for i, item in enumerate(must_see_today, 1):
            lines.extend(render_movie_block(item, i, is_today=True))
            lines.append("")

    if recommended_today:
        lines.extend(["👍 РЕКОМЕНДУЮ", ""])
        for i, item in enumerate(recommended_today, len(must_see_today) + 1):
            lines.extend(render_movie_block(item, i, is_today=True))
            lines.append("")

    if not playing_today:
        lines.append("Сегодня ничего не подходит")
        lines.append("")

    # Coming Week section
    if playing_later:
        lines.extend([
            "┏━━ НА ЭТОЙ НЕДЕЛЕ ━━┓",
            ""
        ])

        must_see_later = [m for m in playing_later if m.get("recommendation") == "must_see"]
        recommended_later = [m for m in playing_later if m.get("recommendation") == "recommended"]

        if must_see_later:
            lines.extend(["🌟 Обязательно", ""])
            for i, item in enumerate(must_see_later, 1):
                lines.extend(render_coming_week_block(item, i))
                lines.append("")

        if recommended_later:
            lines.extend(["👍 Рекомендую", ""])
            for i, item in enumerate(recommended_later, len(must_see_later) + 1):
                lines.extend(render_coming_week_block(item, i))
                lines.append("")

    return "\n".join(lines).rstrip()


def render_movie_block(item: dict, index: int, is_today: bool = True) -> list[str]:
    """Render a movie block. If not today, don't show showtimes."""
    lines = [render_movie_line(item, index)]
    if is_today:
        lines.extend(render_showtime_lines(item.get("movie", {}).get("showtimes", [])))
    return lines


def render_coming_week_block(item: dict, index: int) -> list[str]:
    """Render a movie playing later in the week with available days."""
    lines = [render_movie_line(item, index)]
    movie = item.get("movie", {})
    lines.extend(render_available_days(movie))
    return lines


def render_available_days(movie: dict) -> list[str]:
    """Render available days as a line, preferring accurate data from detail pages."""
    # Prefer accurate days from data-dates attribute
    available_days = movie.get("available_days_accurate", []) or movie.get("available_days", [])

    if not available_days:
        return []

    today_str = datetime.now().strftime("%Y-%m-%d")

    # Filter out today and format dates
    future_days = []
    for day in available_days:
        if day != today_str:
            # Format as DD.MM
            try:
                dt = datetime.strptime(day, "%Y-%m-%d")
                future_days.append(dt.strftime("%d.%m"))
            except ValueError:
                future_days.append(day)

    if not future_days:
        return []

    return [f"📆 {', '.join(future_days)}"]


def render_movie_line(item: dict, index: int) -> str:
    """
    Render a single movie line with markdown.

    Format: [① Title](url) — Score%
    """
    movie = item.get("movie", {})
    title = movie.get("title", "Unknown")
    url = movie.get("url", "")
    score = item.get("relevance_score", 0)

    # Unicode circled numbers
    circled = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
    num = circled[index - 1] if 0 < index <= 20 else f"{index}."

    # Format with markdown link
    if url:
        line = f"[{num} {title}]({url}) — {score}%"
    else:
        line = f"{num} {title} — {score}%"

    return line


def render_showtime_lines(showtimes: list[dict]) -> list[str]:
    if not showtimes:
        return []

    prices = [slot.get("price", "").strip() for slot in showtimes if slot.get("price", "").strip()]
    unique_prices = []
    for price in prices:
        if price not in unique_prices:
            unique_prices.append(price)

    if len(unique_prices) <= 1:
        times = ", ".join(slot.get("time", "") for slot in showtimes if slot.get("time"))
        if times and unique_prices:
            return [f"{times}, {unique_prices[0]}"]
        if times:
            return [times]
        if unique_prices:
            return [unique_prices[0]]
        return []

    lines = []
    for slot in showtimes:
        time_value = slot.get("time", "").strip()
        price_value = slot.get("price", "").strip()
        if time_value and price_value:
            lines.append(f"{time_value}, {price_value}")
        elif time_value:
            lines.append(time_value)
        elif price_value:
            lines.append(price_value)
    return lines


def render_detailed(item: dict) -> str:
    """Render detailed movie info (optional)."""
    movie = item.get("movie", {})
    lines = []

    title = movie.get("title", "")
    director = movie.get("director", "")
    genres = movie.get("genres", [])
    reasoning = item.get("reasoning", "")
    score = item.get("relevance_score", 0)

    lines.append(f"**{title}** — {score}%")
    if director:
        lines.append(f"Реж: {director}")
    if genres:
        lines.append(f"Жанры: {', '.join(genres)}")
    if reasoning:
        lines.append(f"_{reasoning}_")

    return "\n".join(lines)


if __name__ == "__main__":
    # Test rendering
    test_data = [
        {
            "movie": {
                "id": "1",
                "title": "Тестовый фильм",
                "url": "https://example.com/film/1",
                "director": "Режиссер",
                "genres": ["драма"]
            },
            "relevance_score": 85,
            "recommendation": "must_see",
            "reasoning": "Отличный фильм"
        },
        {
            "movie": {
                "id": "2",
                "title": "Хороший фильм",
                "url": "https://example.com/film/2"
            },
            "relevance_score": 70,
            "recommendation": "recommended"
        }
    ]

    print(render_message(test_data, "Набережные Челны"))
