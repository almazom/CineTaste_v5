#!/usr/bin/env python3
"""
ct-analyze/adapter_pi.py — Pi CLI AI Agent Adapter (вилка)

Calls pi CLI to analyze movies against taste profile.
Pure function: movies + taste → analysis results.
"""

import json
import re
import subprocess
import yaml
from pathlib import Path
from typing import Optional


PI_CLI = "pi"


def load_taste_profile(taste_path: str) -> dict:
    """Load taste profile from YAML file."""
    with open(taste_path) as f:
        return yaml.safe_load(f)


def build_prompt(movies: list, taste: dict) -> str:
    """Build analysis prompt for AI agent."""
    likes = taste.get("likes", {})
    dislikes = taste.get("dislikes", {})
    thresholds = taste.get("thresholds", {})

    prompt = """Ты — кинокритик с утонченным вкусом. Проанализируй фильмы и оцени их соответствие вкусу пользователя.

ВКУС ПОЛЬЗОВАТЕЛЯ:

Нравится:
- Режиссеры: {directors}
- Жанры: {genres}
- Ключевые слова: {keywords}

НЕ нравится:
- Жанры: {dislike_genres}
- Ключевые слова: {dislike_keywords}

ФИЛЬМЫ ДЛЯ АНАЛИЗА:
{movies_list}

ЗАДАЧА:
Для каждого фильма верни JSON-объект с анализом:
- movie_id: ID фильма
- relevance_score: число от 0 до 100 (насколько соответствует вкусу)
- recommendation: одно из ["must_see", "recommended", "maybe", "skip"]
- reasoning: краткое объяснение (1-2 предложения)
- key_matches: что совпало со вкусом
- red_flags: что НЕ совпало

ВЕРНИ ТОЛЬКО ВАЛИДНЫЙ JSON-МАССИВ, БЕЗ МАРКДАУН КОДА:
[
  {{
    "movie_id": "...",
    "relevance_score": 85,
    "recommendation": "recommended",
    "reasoning": "...",
    "key_matches": ["..."],
    "red_flags": ["..."]
  }}
]
""".format(
        directors=", ".join(likes.get("directors", [])),
        genres=", ".join(likes.get("genres", [])),
        keywords=", ".join(likes.get("keywords", [])),
        dislike_genres=", ".join(dislikes.get("genres", [])),
        dislike_keywords=", ".join(dislikes.get("keywords", [])),
        movies_list=format_movies_for_prompt(movies)
    )

    return prompt


def format_movies_for_prompt(movies: list) -> str:
    """Format movies list for prompt."""
    lines = []
    for i, m in enumerate(movies, 1):
        line = f"{i}. [{m.get('id', '?')}] {m.get('title', '?')}"
        if m.get("director"):
            line += f" | Реж: {m['director']}"
        if m.get("genres"):
            line += f" | Жанры: {', '.join(m['genres'])}"
        if m.get("year"):
            line += f" | {m['year']}"
        if m.get("raw_description"):
            line += f"\n   Описание: {m['raw_description'][:200]}"
        lines.append(line)
    return "\n".join(lines)


def call_pi(prompt: str, timeout: int = 120) -> str:
    """
    Call pi CLI with prompt.

    Returns:
        AI response text
    """
    try:
        result = subprocess.run(
            [PI_CLI, "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"pi CLI failed: {result.stderr}")

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        raise TimeoutError(f"pi CLI timeout after {timeout}s")
    except FileNotFoundError:
        raise RuntimeError(f"pi CLI not found: {PI_CLI}")


def parse_ai_response(response: str) -> list:
    """
    Parse JSON array from AI response.

    Handles markdown code blocks and extra text.
    """
    # Try direct JSON parse first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON array
    json_match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Try markdown code block
    code_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if code_match:
        try:
            return json.loads(code_match.group(1))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from AI response")


def analyze_movies(movies: list, taste_path: str, dry_run: bool = False) -> list:
    """
    Analyze movies against taste profile.

    Args:
        movies: List of movie dicts from movie-batch
        taste_path: Path to taste/profile.yaml
        dry_run: If True, return mock analysis without calling AI

    Returns:
        List of analysis dicts conforming to analysis-result@1.0.0
    """
    if dry_run:
        return mock_analyze(movies)

    taste = load_taste_profile(taste_path)
    prompt = build_prompt(movies, taste)

    response = call_pi(prompt)
    analyses = parse_ai_response(response)

    # Merge movie data with analysis
    movie_map = {m["id"]: m for m in movies}
    result = []

    for analysis in analyses:
        movie_id = analysis.get("movie_id")
        movie = movie_map.get(movie_id, {})

        result.append({
            "movie": {
                "id": movie.get("id", movie_id),
                "title": movie.get("title", "Unknown"),
                "original_title": movie.get("original_title", ""),
                "director": movie.get("director", ""),
                "actors": movie.get("actors", []),
                "genres": movie.get("genres", []),
                "year": movie.get("year"),
                "source": movie.get("source", ""),
                "url": movie.get("url", "")
            },
            "relevance_score": analysis.get("relevance_score", 50),
            "confidence": 0.8,
            "recommendation": analysis.get("recommendation", "maybe"),
            "reasoning": analysis.get("reasoning", ""),
            "key_matches": analysis.get("key_matches", []),
            "red_flags": analysis.get("red_flags", [])
        })

    return result


def mock_analyze(movies: list) -> list:
    """Generate mock analysis for dry-run mode."""
    result = []

    for movie in movies[:3]:  # Only first 3 for dry-run
        score = 70 + (hash(movie.get("id", "")) % 25)
        rec = "recommended" if score >= 60 else "maybe"

        result.append({
            "movie": {
                "id": movie.get("id", ""),
                "title": movie.get("title", "Unknown"),
                "original_title": movie.get("original_title", ""),
                "director": movie.get("director", ""),
                "actors": movie.get("actors", []),
                "genres": movie.get("genres", []),
                "year": movie.get("year"),
                "source": movie.get("source", ""),
                "url": movie.get("url", "")
            },
            "relevance_score": score,
            "confidence": 0.9,
            "recommendation": rec,
            "reasoning": "Dry run — no AI analysis performed",
            "key_matches": ["dry-run"],
            "red_flags": []
        })

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = json.load(f)

        movies = data.get("movies", [])
        taste_path = sys.argv[2] if len(sys.argv) > 2 else "taste/profile.yaml"

        result = analyze_movies(movies, taste_path, dry_run=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage: python adapter_pi.py <movies.json> [taste.yaml]")
