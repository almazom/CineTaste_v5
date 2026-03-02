#!/usr/bin/env python3
"""
ct-fetch/adapter_kinoteatr.py — Kinoteatr.ru Scraper (вилка)

Fetches movie data from kinoteatr.ru for a given city.
Uses regex-based extraction for robustness.
"""

import re
from datetime import datetime
from typing import List, Dict, Any

import requests


BASE_URL = "https://kinoteatr.ru"

CITY_URLS = {
    "naberezhnie-chelni": "https://kinoteatr.ru/kinoafisha/naberezhnie-chelni/",
    "kazan": "https://kinoteatr.ru/kinoafisha/kazan/",
    "moscow": "https://kinoteatr.ru/kinoafisha/moscow/",
}


def fetch_movies(city: str, when: str = "now") -> List[Dict[str, Any]]:
    """
    Fetch movies from kinoteatr.ru for a given city.

    Args:
        city: City code (e.g., 'naberezhnie-chelni')
        when: Date filter ('now' or 'YYYY-MM-DD')

    Returns:
        List of movie dictionaries
    """
    if city not in CITY_URLS:
        raise ValueError(f"Unknown city: {city}. Available: {list(CITY_URLS.keys())}")

    url = CITY_URLS[city]
    if when != "now":
        url = f"{url}?when={when}"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
    """
    Regex-based extraction of movie info from kinoteatr.ru HTML.

    The HTML structure has:
        <a href="https://kinoteatr.ru/film/film-slug/city/"
           data-gtm-ec-name="Movie Title">
        ...
        data-gtm-list-item-filmName="Movie Title"
        data-gtm-list-item-genre="genre1, genre2"
    """
    movies: List[Dict[str, Any]] = []

    # Pattern 1: Extract from anchor tags with data-gtm-ec-name
    anchor_pattern = re.compile(
        r'<a[^>]*href="(https://kinoteatr\.ru/film/[^"]+)"[^>]*'
        r'data-gtm-ec-name="([^"]+)"[^>]*>',
        re.DOTALL | re.IGNORECASE
    )

    # Extract all anchor info
    anchors = {}
    for match in anchor_pattern.finditer(html):
        url = match.group(1)
        title = match.group(2).strip()
        # Skip non-movie links
        if "podarok" in url.lower() or "подарочн" in title.lower():
            continue
        anchors[title] = url

    # Pattern 2: Extract movie cards with data attributes
    card_pattern = re.compile(
        r'data-gtm-list-item-filmName="([^"]+)"[^>]*'
        r'data-gtm-list-item-genre="([^"]*)"',
        re.DOTALL | re.IGNORECASE
    )

    # Pattern 3: Extract age ratings
    rating_pattern = re.compile(
        r'contentRating">(\d+)\+',
        re.IGNORECASE
    )

    # Get all ratings
    ratings = rating_pattern.findall(html)

    # Process movie cards
    for i, match in enumerate(card_pattern.finditer(html)):
        title = match.group(1).strip()
        genres_raw = match.group(2).strip()

        # Skip non-movies
        if "подарочн" in title.lower():
            continue

        # Get URL from anchors
        url = anchors.get(title, "")

        # Parse genres
        genres = []
        if genres_raw:
            genres = [g.strip() for g in genres_raw.split(',') if g.strip() and len(g.strip()) < 20]

        # Get age rating
        age = ratings[i] if i < len(ratings) else "0"

        # Create movie ID from title
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
            "url": url,
            "raw_description": f"{age}+, {', '.join(genres)}" if genres else f"{age}+"
        }

        # Avoid duplicates
        if not any(m["title"] == title for m in movies):
            movies.append(movie)

    return movies
