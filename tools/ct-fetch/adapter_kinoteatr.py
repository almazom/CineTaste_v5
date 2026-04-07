#!/usr/bin/env python3
"""
ct-fetch/adapter_kinoteatr.py — Kinoteatr.ru Scraper (вилка)

Fetches movie data from kinoteatr.ru for a given city.
Uses regex-based extraction for robustness.
"""

import os
import re
import time
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlencode, urlsplit, urlunsplit

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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _normalize_title_key(value: str) -> str:
    """Normalize title variants so listing cards and clickable anchors can be joined."""
    normalized = value.strip().lower().replace("ё", "е")
    return re.sub(r"\s+", " ", normalized)


def _normalize_listing_base(url: str) -> str:
    """Strip env-provided query params so request URLs are built consistently."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _build_listing_url(city: str, when: str) -> str:
    """Build a normalized kinoteatr listing URL."""
    base_url = _normalize_listing_base(CITY_URLS[city])
    return f"{base_url}?{urlencode({'when': when})}"


def _response_context(response: requests.Response) -> str:
    """Create a short server/context summary for HTTP diagnostics."""
    server = response.headers.get("server", "unknown")
    title_match = re.search(r"<title>([^<]+)</title>", response.text, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else ""
    if title:
        return f"HTTP {response.status_code} via {server} ({title})"
    return f"HTTP {response.status_code} via {server}"


def _fetch_html(url: str, headers: dict[str, str], timeout: int = 30, attempts: int = 3) -> str:
    """Fetch one HTML page with small retry/backoff for transient upstream issues."""
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code in RETRYABLE_STATUS_CODES:
                last_error = requests.HTTPError(
                    f"{_response_context(response)} for url: {url} (attempt {attempt}/{attempts})",
                    response=response,
                )
                if attempt < attempts:
                    time.sleep(2 ** (attempt - 1))
                    continue
                raise last_error

            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            should_retry = isinstance(exc, (requests.Timeout, requests.ConnectionError))
            response = getattr(exc, "response", None)
            if response is not None and response.status_code in RETRYABLE_STATUS_CODES:
                should_retry = True

            if attempt < attempts and should_retry:
                time.sleep(2 ** (attempt - 1))
                continue
            break

    raise ConnectionError(f"Failed to fetch from kinoteatr.ru: {last_error}")


def _extract_anchor_urls(html: str) -> Dict[str, str]:
    """Map normalized anchor titles to movie URLs."""
    anchor_pattern = re.compile(
        r'<a[^>]*href="(https://kinoteatr\.ru/film/[^"]+)"[^>]*'
        r'data-gtm-ec-name="([^"]+)"[^>]*>',
        re.DOTALL | re.IGNORECASE
    )
    return {
        _normalize_title_key(match.group(2)): match.group(1)
        for match in anchor_pattern.finditer(html)
        if "podarok" not in match.group(1).lower()
        and "подарочн" not in match.group(2).lower()
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

    url = _build_listing_url(city, when)
    html = _fetch_html(url, HEADERS, timeout=30, attempts=3)

    return parse_html(html)


def parse_html(html: str) -> List[Dict[str, Any]]:
    """Regex-based extraction of movie info from kinoteatr.ru HTML."""
    movies: List[Dict[str, Any]] = []
    seen_titles: set[str] = set()

    anchors = _extract_anchor_urls(html)

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
        if url := anchors.get(_normalize_title_key(title)):
            movie["url"] = url

        title_key = _normalize_title_key(title)
        if title_key in seen_titles:
            continue

        movies.append(movie)
        seen_titles.add(title_key)

    _enrich_from_detail_pages(movies)
    return movies


def _enrich_from_detail_pages(movies: List[Dict[str, Any]]) -> None:
    """Fetch each movie's detail page to extract director, actors, and accurate available days."""
    for movie in movies:
        url = movie.get("url")
        if not url:
            continue
        try:
            html = _fetch_html(
                url,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
                timeout=10,
                attempts=2,
            )

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

        except (ConnectionError, AttributeError, TypeError):
            pass  # best-effort enrichment


def _fetch_movies_range(city: str, days: int) -> List[Dict[str, Any]]:
    """
    Fetch movies for the next N days and aggregate them.

    Args:
        city: City code
        days: Number of days to fetch

    Returns:
        List of movies with aggregated available days
    """
    from datetime import datetime, timedelta

    if city not in CITY_URLS:
        raise ValueError(f"Unknown city: {city}. Available: {list(CITY_URLS.keys())}")

    base_url = _normalize_listing_base(CITY_URLS[city])
    today = datetime.now()

    # Dict to aggregate movies by ID
    movies_by_id: Dict[str, Dict[str, Any]] = {}

    for day_offset in range(days):
        date = today + timedelta(days=day_offset)
        date_str = date.strftime("%Y-%m-%d")

        url = f"{base_url}?{urlencode({'when': date_str})}"

        try:
            html = _fetch_html(url, HEADERS, timeout=30, attempts=3)
        except ConnectionError as e:
            print(f"Warning: Failed to fetch {date_str}: {e}", file=os.sys.stderr)
            continue

        # Parse movies for this day
        daily_movies = parse_html_with_date(html, date_str, enrich_details=False)

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

    movies = list(movies_by_id.values())
    _enrich_from_detail_pages(movies)
    return movies


def fetch_movies_week(city: str, days: int = 7) -> List[Dict[str, Any]]:
    """Fetch and aggregate the next 7 days of listings."""
    return _fetch_movies_range(city, days=days)


def fetch_movies_month(city: str, days: int = 30) -> List[Dict[str, Any]]:
    """Fetch and aggregate the next 30 days of listings."""
    return _fetch_movies_range(city, days=days)


def parse_html_with_date(html: str, date_str: str, enrich_details: bool = True) -> List[Dict[str, Any]]:
    """
    Parse HTML and track which days each movie is available.
    Similar to parse_html but tracks available days for week aggregation.
    """
    movies: List[Dict[str, Any]] = []
    seen_titles: set[str] = set()
    movies_by_id: Dict[str, Dict[str, Any]] = {}

    anchors = _extract_anchor_urls(html)

    # Extract movie cards with showtime info
    # Look for movie cards that contain showtimes
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
            "raw_description": f"{age}+, {', '.join(genres)}" if genres else f"{age}+",
            "available_days": [date_str]
        }

        title_key = _normalize_title_key(title)
        if url := anchors.get(title_key):
            movie["url"] = url

        if title_key in seen_titles:
            # Movie already exists, just add this date to its available_days
            existing_movie = movies_by_id.get(movie_id)
            if existing_movie:
                existing_movie.setdefault("available_days", []).append(date_str)
            continue

        movies.append(movie)
        seen_titles.add(title_key)
        movies_by_id[movie_id] = movie

    if enrich_details:
        _enrich_from_detail_pages(movies)
    return movies
