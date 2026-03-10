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
    """Render filtered movies as Telegram markdown."""
    if not date:
        date = datetime.now().strftime("%d.%m.%Y")

    lines = [
        f"📅 {date}",
        "",
        "┏━━ СЕГОДНЯ ━━┓",
        ""
    ]

    must_see = [m for m in filtered if m.get("recommendation") == "must_see"]
    recommended = [m for m in filtered if m.get("recommendation") == "recommended"]

    if must_see:
        lines.extend(["🌟 ОБЯЗАТЕЛЬНО", ""])
        lines.extend(render_movie_line(item, i) for i, item in enumerate(must_see, 1))
        lines.append("")

    if recommended:
        lines.extend(["👍 РЕКОМЕНДУЮ", ""])
        lines.extend(render_movie_line(item, i) for i, item in enumerate(recommended, len(must_see) + 1))
        lines.append("")

    lines.extend([
        "┏━━ 📊 ━━┓",
        f"{len(filtered)} фильмов подходит",
        "",
        f"📍 {city_display}"
    ])

    return "\n".join(lines)


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
