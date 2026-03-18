#!/usr/bin/env python3
"""
ct-fetch/adapter_kinoteatr.py — Kinoteatr.ru Scraper (вилка)

Fetches movie data from kinoteatr.ru for a given city.
Uses regex-based extraction for robustness.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any

import requests
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOTENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(DOTENV_PATH)

# Single city: Набережные Челны (from .env)
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "naberezhnie-chelni")
DEFAULT_CINEMA_URL = os.getenv("DEFAULT_CINEMA_URL", "https://kinoteatr.ru/kinoafisha/naberezhnie-chelni/")

CITY_URLS = {
    DEFAULT_CITY: DEFAULT_CINEMA_URL,
}


def fetch_movies(city: str, when: str = "now") -> List[Dict[str, Any]]:
    """
    Fetch movies from kinoteatr.ru for a given city.

    Args:
        city: City code (e.g., 'naberezhnie-chelni')
        when: Date filter ('now', 'week', or 'YYYY-MM-DD')

    Returns:
        List of movie dictionaries
    """
    if when == "week":
        return fetch_movies_week(city)

    if city not in CITY_URLS:
        raise ValueError(f"Unknown city: {city}. Available: {list(CITY_URLS.keys())}")

    url = CITY_URLS[city]
    if when != "now":
        url = f"{url}?when={when}"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text
    except requests.RequestException as e:
        raise ConnectionError(f"Failed to fetch from kinoteatr.ru: {e}")

    return parse_html(html)


def parse_html(html: str) -> List[Dict[str, Any]]:
    """Regex-based extraction of movie info from kinoteatr.ru HTML."""
    movies: List[Dict[str, Any]] = []
    seen_titles: set[str] = set()

    # Extract anchor URLs
    anchor_pattern = re.compile(
        r'<a[^>]*href="(https://kinoteatr\.ru/film/[^"]+)"[^>]*'
        r'data-gtm-ec-name="([^"]+)"[^>]*>',
        re.DOTALL | re.IGNORECASE
    )
    anchors = {m.group(2).strip(): m.group(1) for m in anchor_pattern.finditer(html)
               if "podarok" not in m.group(1).lower() and "подарочн" not in m.group(2).lower()}

    # Extract movie cards
    card_pattern = re.compile(
        r'data-gtm-list-item-filmName="([^"]+)"[^>]*'
        r'data-gtm-list-item-genre="([^"]*)"',
        re.DOTALL | re.IGNORECASE
    )
    rating_pattern = re.compile(r'contentRating">(\d+)\+', re.IGNORECASE)
    ratings = rating_pattern.findall(html)

    for i, match in enumerate(card_pattern.finditer(html)):
        title = match.group(1).strip()
        if "подарочн" in title.lower():
            continue

        genres_raw = match.group(2).strip()
        genres = [g.strip() for g in genres_raw.split(',') if g.strip() and len(g.strip()) < 20]
        age = ratings[i] if i < len(ratings) else "0"
        movie_id = re.sub(r"[^\w]", "-", title.lower())[:50]

        movie: Dict[str, Any] = {
            "id": f"kt-{movie_id}",
            "title": title,
            "original_title": "",
            "director": "",
            "actors": [],
            "genres": genres,
            "year": None,
            "duration_min": None,
            "source": "kinoteatr.ru",
            "raw_description": f"{age}+, {', '.join(genres)}" if genres else f"{age}+"
        }
        if url := anchors.get(title):
            movie["url"] = url

        if title in seen_titles:
            continue

        movies.append(movie)
        seen_titles.add(title)

    _enrich_from_detail_pages(movies)
    return movies


def _enrich_from_detail_pages(movies: List[Dict[str, Any]]) -> None:
    """Fetch each movie's detail page to extract director, actors, and accurate available days."""
    for movie in movies:
        url = movie.get("url")
        if not url:
            continue
        try:
            resp = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            }, timeout=10)
            resp.raise_for_status()
            html = resp.text

            # Director via schema.org itemprop
            d = re.search(
                r'itemprop="director"[^>]*>.*?itemprop="name">([^<]+)',
                html, re.DOTALL
            )
            if d:
                movie["director"] = d.group(1).strip()

            # Actors via schema.org itemprop inside movie_actors block
            actors_block = re.search(
                r'class="movie_actors">В ролях.*?<td[^>]*>(.*?)</td>',
                html, re.DOTALL
            )
            if actors_block:
                movie["actors"] = re.findall(
                    r'itemprop="name">([^<]+)', actors_block.group(1)
                )

            # Extract accurate available days from data-dates attribute
            # This is the source of truth for when movie actually plays
            data_dates_match = re.search(
                r'data-dates="([^"]+)"',
                html
            )
            if data_dates_match:
                dates_str = data_dates_match.group(1)
                # Parse comma-separated dates
                accurate_dates = [d.strip() for d in dates_str.split(',') if d.strip()]
                if accurate_dates:
                    movie["available_days_accurate"] = accurate_dates

        except (requests.RequestException, AttributeError, TypeError):
            pass  # best-effort enrichment


def fetch_movies_week(city: str, days: int = 7) -> List[Dict[str, Any]]:
    """
    Fetch movies for the next N days and aggregate them.

    Args:
        city: City code
        days: Number of days to fetch (default: 7)

    Returns:
        List of movies with showtimes_by_day field
    """
    from datetime import datetime, timedelta

    if city not in CITY_URLS:
        raise ValueError(f"Unknown city: {city}. Available: {list(CITY_URLS.keys())}")

    base_url = CITY_URLS[city]
    today = datetime.now()

    # Dict to aggregate movies by ID
    movies_by_id: Dict[str, Dict[str, Any]] = {}

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    for day_offset in range(days):
        date = today + timedelta(days=day_offset)
        date_str = date.strftime("%Y-%m-%d")

        url = f"{base_url}?when={date_str}"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            html = response.text
        except requests.RequestException as e:
            print(f"Warning: Failed to fetch {date_str}: {e}", file=os.sys.stderr)
            continue

        # Parse movies for this day
        daily_movies = parse_html_with_date(html, date_str)

        # Merge into aggregated dict
        for movie in daily_movies:
            movie_id = movie["id"]

            if movie_id not in movies_by_id:
                movies_by_id[movie_id] = movie
            else:
                # Merge available days
                existing_days = set(movies_by_id[movie_id].get("available_days", []))
                new_days = set(movie.get("available_days", []))
                movies_by_id[movie_id]["available_days"] = sorted(existing_days | new_days)

    return list(movies_by_id.values())


def parse_html_with_date(html: str, date_str: str) -> List[Dict[str, Any]]:
    """
    Parse HTML and track which days each movie is available.
    Similar to parse_html but tracks available days for week aggregation.
    """
    movies: List[Dict[str, Any]] = []
    seen_titles: set[str] = set()
    movies_by_id: Dict[str, Dict[str, Any]] = {}

    # Extract anchor URLs
    anchor_pattern = re.compile(
        r'<a[^>]*href="(https://kinoteatr\.ru/film/[^"]+)"[^>]*'
        r'data-gtm-ec-name="([^"]+)"[^>]*>',
        re.DOTALL | re.IGNORECASE
    )
    anchors = {m.group(2).strip(): m.group(1) for m in anchor_pattern.finditer(html)
               if "podarok" not in m.group(1).lower() and "подарочн" not in m.group(2).lower()}

    # Extract movie cards with showtime info
    # Look for movie cards that contain showtimes
    card_pattern = re.compile(
        r'data-gtm-list-item-filmName="([^"]+)"[^>]*'
        r'data-gtm-list-item-genre="([^"]*)"',
        re.DOTALL | re.IGNORECASE
    )
    rating_pattern = re.compile(r'contentRating">(\d+)\+', re.IGNORECASE)
    ratings = rating_pattern.findall(html)

    # Find showtimes section for each movie
    # The HTML structure has movie cards with embedded showtimes
    showtime_pattern = re.compile(
        r'data-gtm-list-item-filmName="([^"]+)".*?'
        r'<div[^>]*class="sessions[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>',
        re.DOTALL | re.IGNORECASE
    )

    showtime_time_pattern = re.compile(
        r'<a[^>]*data-gtm-ec-name="(\d{2}:\d{2})"[^>]*>.*?'
        r'(?:data-gtm-ec-price="([^"]*)"|цена[^>]*>)?',
        re.DOTALL | re.IGNORECASE
    )

    for i, match in enumerate(card_pattern.finditer(html)):
        title = match.group(1).strip()
        if "подарочн" in title.lower():
            continue

        genres_raw = match.group(2).strip()
        genres = [g.strip() for g in genres_raw.split(',') if g.strip() and len(g.strip()) < 20]
        age = ratings[i] if i < len(ratings) else "0"
        movie_id = re.sub(r"[^\w]", "-", title.lower())[:50]

        movie: Dict[str, Any] = {
            "id": f"kt-{movie_id}",
            "title": title,
            "original_title": "",
            "director": "",
            "actors": [],
            "genres": genres,
            "year": None,
            "duration_min": None,
            "source": "kinoteatr.ru",
            "raw_description": f"{age}+, {', '.join(genres)}" if genres else f"{age}+",
            "available_days": [date_str]
        }

        if url := anchors.get(title):
            movie["url"] = url

        if title in seen_titles:
            # Movie already exists, just add this date to its available_days
            existing_movie = movies_by_id.get(movie_id)
            if existing_movie:
                existing_movie.setdefault("available_days", []).append(date_str)
            continue

        movies.append(movie)
        seen_titles.add(title)
        movies_by_id[movie_id] = movie

    _enrich_from_detail_pages(movies)
    return movies
