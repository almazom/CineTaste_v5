#!/usr/bin/env python3
"""
ct-format/adapter_telegram.py — Telegram Markdown Renderer (вилка)

Renders filtered movies as Telegram markdown message.
Pure function: data in → markdown out.
"""

from datetime import date, datetime
from typing import Optional


def render_message(
    filtered: list,
    city_display: str,
    date: Optional[str] = None
) -> str:
    """Render filtered movies as Telegram markdown with 1-day, 7-day, and 30-day horizons."""
    if not date:
        date = datetime.now().strftime("%d.%m.%Y")

    base_date = datetime.now().date()
    today_entries, week_entries, month_entries = split_by_horizon(filtered, base_date)

    lines = [
        f"📅 {date}",
        "",
        "┏━━ СЕГОДНЯ ━━┓",
        ""
    ]

    must_see_today = [entry for entry in today_entries if entry["item"].get("recommendation") == "must_see"]
    recommended_today = [entry for entry in today_entries if entry["item"].get("recommendation") == "recommended"]

    if must_see_today:
        lines.extend(["🌟 ОБЯЗАТЕЛЬНО", ""])
        for i, entry in enumerate(must_see_today, 1):
            lines.extend(render_movie_block(entry["item"], i, is_today=True))
            lines.append("")

    if recommended_today:
        lines.extend(["👍 РЕКОМЕНДУЮ", ""])
        for i, entry in enumerate(recommended_today, len(must_see_today) + 1):
            lines.extend(render_movie_block(entry["item"], i, is_today=True))
            lines.append("")

    if not today_entries:
        lines.append("Сегодня ничего не подходит")
        lines.append("")

    lines.extend([
        "┏━━ В БЛИЖАЙШИЕ 7 ДНЕЙ ━━┓",
        ""
    ])

    if week_entries:
        must_see_week = [entry for entry in week_entries if entry["item"].get("recommendation") == "must_see"]
        recommended_week = [entry for entry in week_entries if entry["item"].get("recommendation") == "recommended"]

        if must_see_week:
            lines.extend(["🌟 Обязательно", ""])
            for i, entry in enumerate(must_see_week, 1):
                lines.extend(render_future_block(entry["item"], i, entry["dates"], base_date))
                lines.append("")

        if recommended_week:
            lines.extend(["👍 Рекомендую", ""])
            for i, entry in enumerate(recommended_week, len(must_see_week) + 1):
                lines.extend(render_future_block(entry["item"], i, entry["dates"], base_date))
                lines.append("")
    else:
        lines.extend(["В ближайшие 7 дней ничего не подходит", ""])

    lines.extend([
        "┏━━ В БЛИЖАЙШИЕ 30 ДНЕЙ ━━┓",
        ""
    ])

    if month_entries:
        must_see_month = [entry for entry in month_entries if entry["item"].get("recommendation") == "must_see"]
        recommended_month = [entry for entry in month_entries if entry["item"].get("recommendation") == "recommended"]

        if must_see_month:
            lines.extend(["🌟 Обязательно", ""])
            for i, entry in enumerate(must_see_month, 1):
                lines.extend(render_future_block(entry["item"], i, entry["dates"], base_date))
                lines.append("")

        if recommended_month:
            lines.extend(["👍 Рекомендую", ""])
            for i, entry in enumerate(recommended_month, len(must_see_month) + 1):
                lines.extend(render_future_block(entry["item"], i, entry["dates"], base_date))
                lines.append("")
    else:
        lines.extend(["В ближайшие 30 дней ничего не подходит", ""])

    return "\n".join(lines).rstrip()


def split_by_horizon(filtered: list, base_date: date) -> tuple[list[dict], list[dict], list[dict]]:
    """Split filtered movies into today, next-7-days, and next-30-days buckets."""
    today_entries: list[dict] = []
    week_entries: list[dict] = []
    month_entries: list[dict] = []

    for item in filtered:
        play_dates = extract_play_dates(item.get("movie", {}))
        today_dates = [d for d in play_dates if (d - base_date).days == 0]
        week_dates = [d for d in play_dates if 1 <= (d - base_date).days <= 7]
        month_dates = [d for d in play_dates if 8 <= (d - base_date).days <= 30]

        if today_dates:
            today_entries.append({"item": item, "dates": today_dates})
        elif week_dates:
            week_entries.append({"item": item, "dates": week_dates})
        elif month_dates:
            month_entries.append({"item": item, "dates": month_dates})
        else:
            # Backward-compatible fallback for minimal payloads without any date metadata.
            today_entries.append({"item": item, "dates": []})

    return today_entries, week_entries, month_entries


def extract_play_dates(movie: dict) -> list[date]:
    """Collect unique play dates from accurate days, aggregated days, or showtimes."""
    raw_values = movie.get("available_days_accurate", []) or movie.get("available_days", [])
    parsed = {_parse_iso_date(value) for value in raw_values}
    parsed.discard(None)

    if not parsed:
        for slot in movie.get("showtimes", []):
            datetime_iso = str(slot.get("datetime_iso", "")).strip()
            if not datetime_iso:
                continue
            parsed_date = _parse_iso_date(datetime_iso[:10])
            if parsed_date is not None:
                parsed.add(parsed_date)

    return sorted(parsed)


def _parse_iso_date(value: str) -> Optional[date]:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def render_movie_block(item: dict, index: int, is_today: bool = True) -> list[str]:
    """Render a movie block. If not today, don't show showtimes."""
    lines = [render_movie_line(item, index)]
    if is_today:
        lines.extend(render_showtime_lines(item.get("movie", {}).get("showtimes", [])))
    return lines


def render_future_block(item: dict, index: int, dates: list[date], base_date: date) -> list[str]:
    """Render a future movie block with filtered available days for its horizon bucket."""
    lines = [render_movie_line(item, index)]
    lines.extend(render_available_days(dates, base_date))
    return lines


def render_available_days(dates: list[date], base_date: date) -> list[str]:
    """Render selected future dates plus the nearest human-readable distance."""
    if not dates:
        return []

    lines = [f"📆 {', '.join(day.strftime('%d.%m') for day in dates)}"]
    nearest_date = min(dates)
    relative_label = describe_relative_distance(nearest_date, base_date)
    if relative_label:
        lines.append(f"⏳ {relative_label}")
    return lines


def describe_relative_distance(target_date: date, base_date: date) -> str:
    """Describe distance from today in short natural Russian."""
    day_delta = (target_date - base_date).days
    if day_delta <= 0:
        return ""
    if day_delta == 1:
        return "завтра"
    if day_delta == 2:
        return "послезавтра"
    if day_delta == 7:
        return "через неделю"
    if day_delta in {14, 21, 28}:
        weeks = day_delta // 7
        return f"через {weeks} {pluralize_ru(weeks, 'неделю', 'недели', 'недель')}"
    return f"через {day_delta} {pluralize_ru(day_delta, 'день', 'дня', 'дней')}"


def pluralize_ru(value: int, singular: str, paucal: str, plural: str) -> str:
    """Return a Russian plural form for the given integer."""
    mod100 = value % 100
    mod10 = value % 10
    if 11 <= mod100 <= 14:
        return plural
    if mod10 == 1:
        return singular
    if 2 <= mod10 <= 4:
        return paucal
    return plural


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
