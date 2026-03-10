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
    """Fetch each movie's detail page to extract director and actors."""
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
        except (requests.RequestException, AttributeError, TypeError):
            pass  # best-effort enrichment
