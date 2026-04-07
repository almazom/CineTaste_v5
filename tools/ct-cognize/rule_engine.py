#!/usr/bin/env python3
"""
rules-first scoring helpers for ct-cognize.
"""

from __future__ import annotations

import re
from typing import Any


RECOMMENDATION_ORDER = {
    "skip": 0,
    "maybe": 1,
    "recommended": 2,
    "must_see": 3,
}

DEFAULT_THRESHOLDS = {
    "must_see": 85,
    "recommended": 60,
    "maybe": 40,
    "skip": 0,
}

TERM_ALIASES = {
    "anime": {
        "anime",
        "аниме",
        "japanese anime",
        "japanese animation",
        "японское аниме",
        "анимация японии",
    },
    "drama": {
        "drama",
        "драма",
        "independent drama",
        "indie drama",
        "psychological drama",
        "social drama",
        "festival drama",
    },
    "horror": {
        "horror",
        "ужасы",
    },
    "slasher": {
        "slasher",
        "слешер",
        "слэшер",
    },
    "science fiction": {
        "science fiction",
        "sci fi",
        "sci-fi",
        "научная фантастика",
        "фантастика",
    },
    "franchise": {
        "franchise",
        "франшиза",
    },
    "sequel": {
        "sequel",
        "сиквел",
        "продолжение",
        "часть 2",
    },
    "remake": {
        "remake",
        "ремейк",
    },
    "blockbuster": {
        "blockbuster",
        "блокбастер",
    },
    "modern russian cinema": {
        "modern russian cinema",
        "современное российское кино",
        "современное русское кино",
        "российское кино",
        "русское кино",
    },
}

ALIAS_TO_CANON = {
    alias: canon
    for canon, aliases in TERM_ALIASES.items()
    for alias in aliases
}

ZERO_WIDTH_PATTERN = re.compile(r"[\u200b-\u200f\u2060\ufeff]")

ANIME_CREATOR_DESCRIPTORS = [
    {
        "label": "Hayao Miyazaki",
        "aliases": ["hayao miyazaki", "miyazaki", "хаяо миядзаки", "миядзаки"],
    },
    {
        "label": "Makoto Shinkai",
        "aliases": ["makoto shinkai", "shinkai", "макото синкай", "синкай"],
    },
    {
        "label": "Mamoru Hosoda",
        "aliases": ["mamoru hosoda", "hosoda", "мамору хосода", "хосода"],
    },
    {
        "label": "Satoshi Kon",
        "aliases": ["satoshi kon", "kon", "сатоси кон", "сатоши кон"],
    },
    {
        "label": "Mamoru Oshii",
        "aliases": ["mamoru oshii", "oshii", "мамору осии", "осии"],
    },
    {
        "label": "Shoji Kawamori",
        "aliases": ["shoji kawamori", "kawamori", "седзи кавамори", "сёдзи кавамори", "кавамори"],
    },
    {
        "label": "Hiroyuki Morita",
        "aliases": ["hiroyuki morita", "morita", "хироюки морита", "морита"],
    },
]


def normalize_text(value: Any) -> str:
    """Normalize text for fuzzy matching."""
    if value is None:
        return ""
    normalized = ZERO_WIDTH_PATTERN.sub("", str(value)).strip().lower().replace("ё", "е")
    normalized = re.sub(r"[^\w\s-]+", " ", normalized, flags=re.UNICODE)
    return re.sub(r"\s+", " ", normalized).strip()


def canonicalize_term(value: Any) -> str:
    """Return canonical term when an alias is known."""
    normalized = normalize_text(value)
    return ALIAS_TO_CANON.get(normalized, normalized)


def unique_strings(values: list[str]) -> list[str]:
    """Keep first-seen order while dropping empties and duplicates."""
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value).strip()
        key = normalize_text(cleaned)
        if not cleaned or not key or key in seen:
            continue
        ordered.append(cleaned)
        seen.add(key)
    return ordered


def clamp(value: float, lower: float, upper: float) -> float:
    """Clamp a numeric value into a closed interval."""
    return max(lower, min(upper, value))


def recommendation_from_score(score: float, thresholds: dict[str, int]) -> str:
    """Convert a numeric score to a recommendation label."""
    if score >= thresholds["must_see"]:
        return "must_see"
    if score >= thresholds["recommended"]:
        return "recommended"
    if score >= thresholds["maybe"]:
        return "maybe"
    return "skip"


def stronger_recommendation(left: str | None, right: str | None) -> str | None:
    """Return the stronger recommendation."""
    if not left:
        return right
    if not right:
        return left
    return left if RECOMMENDATION_ORDER[left] >= RECOMMENDATION_ORDER[right] else right


def weaker_recommendation(left: str | None, right: str | None) -> str | None:
    """Return the weaker recommendation."""
    if not left:
        return right
    if not right:
        return left
    return left if RECOMMENDATION_ORDER[left] <= RECOMMENDATION_ORDER[right] else right


def apply_recommendation_bounds(
    recommendation: str,
    floor: str | None,
    ceiling: str | None,
) -> str:
    """Apply floor and ceiling bounds to one recommendation label."""
    bounded = recommendation
    if floor and RECOMMENDATION_ORDER[bounded] < RECOMMENDATION_ORDER[floor]:
        bounded = floor
    if ceiling and RECOMMENDATION_ORDER[bounded] > RECOMMENDATION_ORDER[ceiling]:
        bounded = ceiling
    return bounded


def score_for_recommendation(
    recommendation: str,
    thresholds: dict[str, int],
) -> int:
    """Return a representative score inside a recommendation band."""
    if recommendation == "must_see":
        return max(thresholds["must_see"], 90)
    if recommendation == "recommended":
        return max(thresholds["recommended"], 70)
    if recommendation == "maybe":
        return max(thresholds["maybe"], 50)
    return min(thresholds["maybe"] - 5, 25)


def fit_score_to_recommendation(
    score: int,
    recommendation: str,
    thresholds: dict[str, int],
) -> int:
    """Clamp a score into the numeric band implied by one recommendation."""
    if recommendation == "must_see":
        return int(clamp(score, thresholds["must_see"], 100))
    if recommendation == "recommended":
        return int(clamp(score, thresholds["recommended"], thresholds["must_see"] - 1))
    if recommendation == "maybe":
        return int(clamp(score, thresholds["maybe"], thresholds["recommended"] - 1))
    return int(clamp(score, 0, thresholds["maybe"] - 1))


def make_person_descriptor(label: str) -> dict[str, Any]:
    """Build a fuzzy person matcher from a profile name."""
    normalized = normalize_text(label)
    parts = normalized.split()
    aliases = {normalized}
    if len(parts) > 1 and len(parts[-1]) >= 4:
        aliases.add(parts[-1])
    return {"label": label, "aliases": sorted(aliases)}


def make_keyword_descriptor(label: str) -> dict[str, Any]:
    """Build a keyword matcher with alias expansion."""
    normalized = normalize_text(label)
    aliases = {normalized}
    canonical = canonicalize_term(label)
    aliases.add(canonical)
    if canonical in TERM_ALIASES:
        aliases.update(TERM_ALIASES[canonical])
    return {"label": label, "aliases": sorted(a for a in aliases if a)}


def _present_values(values: list[Any] | None) -> list[str]:
    """Keep only non-empty string values from profile arrays."""
    return [str(value) for value in values or [] if str(value).strip()]


def _compile_people(values: list[Any] | None) -> list[dict[str, Any]]:
    """Compile person-name arrays into fuzzy descriptors."""
    return [make_person_descriptor(value) for value in _present_values(values)]


def _compile_keywords(values: list[Any] | None) -> list[dict[str, Any]]:
    """Compile keyword-like arrays into alias-expanded descriptors."""
    return [make_keyword_descriptor(value) for value in _present_values(values)]


def _compile_term_set(values: list[Any] | None) -> set[str]:
    """Compile a profile list into a canonical normalized term set."""
    return {canonicalize_term(value) for value in _present_values(values)}


def compile_taste_profile(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Compile taste YAML into normalized structures for deterministic scoring."""
    payload = payload or {}
    likes = payload.get("likes") or {}
    dislikes = payload.get("dislikes") or {}
    canon = payload.get("canon") or []
    thresholds = {**DEFAULT_THRESHOLDS, **(payload.get("thresholds") or {})}

    compiled_canon = []
    for item in canon:
        if not isinstance(item, dict):
            continue
        director = str(item.get("director", "")).strip()
        if not director:
            continue
        descriptor = make_person_descriptor(director)
        descriptor["weight"] = float(item.get("weight", 1.0))
        compiled_canon.append(descriptor)

    return {
        "thresholds": thresholds,
        "liked_directors": _compile_people(likes.get("directors")),
        "favorite_actors": _compile_people(likes.get("actors")),
        "canon_directors": compiled_canon,
        "anime_creators": ANIME_CREATOR_DESCRIPTORS,
        "likes_anime": "anime" in _compile_term_set(likes.get("genres")),
        "liked_genres": _compile_term_set(likes.get("genres")),
        "disliked_genres": _compile_term_set(dislikes.get("genres")),
        "liked_keywords": _compile_keywords(likes.get("keywords")),
        "disliked_keywords": _compile_keywords(dislikes.get("keywords")),
        "liked_regions": _compile_keywords(likes.get("regions")),
        "disliked_regions": _compile_keywords(dislikes.get("regions")),
        "liked_eras": _compile_keywords(likes.get("eras")),
        "disliked_eras": _compile_keywords(dislikes.get("eras")),
    }


def movie_text_blob(movie: dict[str, Any]) -> str:
    """Combine movie metadata into one normalized search blob."""
    parts: list[str] = [
        str(movie.get("title", "")),
        str(movie.get("original_title", "")),
        str(movie.get("director", "")),
        str(movie.get("raw_description", "")),
    ]
    parts.extend(str(value) for value in movie.get("actors", []) or [])
    parts.extend(str(value) for value in movie.get("genres", []) or [])
    return normalize_text(" ".join(parts))


def movie_genre_set(movie: dict[str, Any]) -> set[str]:
    """Normalize movie genres into canonical tags."""
    return {
        canonicalize_term(value)
        for value in movie.get("genres", []) or []
        if str(value).strip()
    }


def match_descriptors(descriptors: list[dict[str, Any]], text: str) -> list[str]:
    """Return profile labels whose aliases occur in text."""
    matches: list[str] = []
    for descriptor in descriptors:
        if any(alias and alias in text for alias in descriptor["aliases"]):
            matches.append(descriptor["label"])
    return unique_strings(matches)


def metadata_confidence(movie: dict[str, Any]) -> float:
    """Estimate metadata richness on a 0..1 scale."""
    score = 0.25
    if normalize_text(movie.get("director")):
        score += 0.18
    if movie.get("actors"):
        score += 0.18
    if movie.get("genres"):
        score += 0.18
    if len(normalize_text(movie.get("raw_description"))) >= 24:
        score += 0.14
    if normalize_text(movie.get("original_title")):
        score += 0.07
    return round(clamp(score, 0.0, 1.0), 2)


def has_sequel_marker(movie: dict[str, Any], blob: str) -> bool:
    """Detect a likely sequel marker in title or metadata."""
    title = normalize_text(movie.get("title"))
    if re.search(r"(?:^|\s)(2|3|4|5|ii|iii|iv|v)(?:\s|$|:)", title):
        return True
    return any(marker in blob for marker in ("сиквел", "sequel", "часть 2", "part 2"))


def build_rule_score(movie: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Score one movie with deterministic taste rules."""
    thresholds = profile["thresholds"]
    blob = movie_text_blob(movie)
    genres = movie_genre_set(movie)
    director_text = normalize_text(movie.get("director"))
    actors_text = normalize_text(" ".join(movie.get("actors", []) or []))
    year = movie.get("year")

    score = 18.0
    floor: str | None = None
    ceiling: str | None = None
    strong_positive = False
    hard_negative = False
    matches: list[str] = []
    penalties: list[str] = []
    basis: list[str] = []

    canon_hits = []
    for descriptor in profile["canon_directors"]:
        if any(alias in director_text for alias in descriptor["aliases"]):
            canon_hits.append(descriptor)
    if canon_hits:
        best = max(canon_hits, key=lambda item: item["weight"])
        score = max(score, 88 + round(best["weight"] * 8))
        floor = stronger_recommendation(floor, "must_see")
        strong_positive = True
        matches.append(f"канон: {best['label']}")
        basis.append("rule:canon_floor")

    anime_match = "anime" in genres or "anime" in blob
    if anime_match:
        score = max(score, 90)
        floor = stronger_recommendation(floor, "must_see")
        strong_positive = True
        matches.append("аниме")
        basis.append("rule:anime_floor")

    anime_creator_hits = []
    if profile.get("likes_anime"):
        anime_creator_hits = match_descriptors(profile["anime_creators"], director_text)
    if anime_creator_hits:
        score = max(score, thresholds["recommended"] + 2)
        floor = stronger_recommendation(floor, "recommended")
        matches.extend(f"аниме-автор: {label}" for label in anime_creator_hits)
        basis.append("rule:anime_creator")

    liked_director_hits = match_descriptors(profile["liked_directors"], director_text)
    if liked_director_hits:
        score += min(18, 10 + 4 * len(liked_director_hits))
        floor = stronger_recommendation(floor, "recommended")
        matches.extend(f"режиссер: {label}" for label in liked_director_hits)
        basis.append("rule:director_match")

    actor_hits = match_descriptors(profile["favorite_actors"], actors_text)
    if actor_hits:
        score += min(18, 12 + 4 * (len(actor_hits) - 1))
        floor = stronger_recommendation(floor, "recommended")
        matches.extend(f"актер: {label}" for label in actor_hits)
        basis.append("rule:actor_bonus")

    liked_genre_hits = sorted(profile["liked_genres"] & genres)
    if liked_genre_hits:
        score += min(20, 6 * len(liked_genre_hits))
        if len(liked_genre_hits) >= 2:
            floor = stronger_recommendation(floor, "recommended")
        matches.extend(f"жанр: {label}" for label in liked_genre_hits)
        basis.append("rule:genre_match")

    liked_keyword_hits = (
        match_descriptors(profile["liked_keywords"], blob)
        + match_descriptors(profile["liked_regions"], blob)
        + match_descriptors(profile["liked_eras"], blob)
    )
    liked_keyword_hits = unique_strings(liked_keyword_hits)
    if liked_keyword_hits:
        score += min(16, 4 * len(liked_keyword_hits))
        matches.extend(f"ключ: {label}" for label in liked_keyword_hits[:4])
        basis.append("rule:keyword_match")

    disliked_genre_hits = sorted(profile["disliked_genres"] & genres)
    if disliked_genre_hits:
        penalty = 18 if strong_positive else 28
        score -= min(42, penalty + 8 * (len(disliked_genre_hits) - 1))
        penalties.extend(f"антижанр: {label}" for label in disliked_genre_hits)
        basis.append("rule:genre_penalty")
        if any(label in {"horror", "slasher"} for label in disliked_genre_hits) and not strong_positive:
            ceiling = weaker_recommendation(ceiling, "skip")
            hard_negative = True
            basis.append("rule:horror_ceiling")

    disliked_keyword_hits = (
        match_descriptors(profile["disliked_keywords"], blob)
        + match_descriptors(profile["disliked_regions"], blob)
        + match_descriptors(profile["disliked_eras"], blob)
    )
    disliked_keyword_hits = unique_strings(disliked_keyword_hits)
    if disliked_keyword_hits:
        score -= min(30, 10 + 6 * (len(disliked_keyword_hits) - 1))
        penalties.extend(f"антисигнал: {label}" for label in disliked_keyword_hits[:4])
        basis.append("rule:keyword_penalty")
        if not strong_positive and any(label in {"blockbuster", "franchise", "remake"} for label in map(canonicalize_term, disliked_keyword_hits)):
            ceiling = weaker_recommendation(ceiling, "recommended")
            basis.append("rule:commercial_ceiling")

    if has_sequel_marker(movie, blob) and not strong_positive:
        score -= 8
        penalties.append("сиквел/часть")
        ceiling = weaker_recommendation(ceiling, "recommended")
        basis.append("rule:sequel_penalty")

    if (
        year is not None
        and int(year) >= 1990
        and any(marker in blob for marker in TERM_ALIASES["modern russian cinema"])
        and not strong_positive
    ):
        score -= 35
        penalties.append("современное российское кино")
        ceiling = weaker_recommendation(ceiling, "skip")
        hard_negative = True
        basis.append("rule:modern_russian_ceiling")

    metadata_score = metadata_confidence(movie)
    if metadata_score < 0.45:
        score -= 6
        penalties.append("скудные метаданные")
        basis.append("quality:sparse_metadata")

    rule_score = int(round(clamp(score, 0, 100)))
    bounded_recommendation = recommendation_from_score(rule_score, thresholds)
    bounded_recommendation = apply_recommendation_bounds(bounded_recommendation, floor, ceiling)
    rule_score = fit_score_to_recommendation(rule_score, bounded_recommendation, thresholds)

    return {
        "movie_id": movie.get("id", ""),
        "rule_score": int(rule_score),
        "recommendation_floor": floor,
        "recommendation_ceiling": ceiling,
        "rule_recommendation": bounded_recommendation,
        "key_rule_matches": unique_strings(matches),
        "key_rule_penalties": unique_strings(penalties),
        "decision_basis": unique_strings(basis),
        "metadata_confidence": metadata_score,
        "strong_positive": strong_positive,
        "hard_negative": hard_negative,
    }


def build_rule_map(movies: list[dict[str, Any]], taste_payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Build deterministic rule signals keyed by movie id."""
    profile = compile_taste_profile(taste_payload)
    return {
        movie.get("id", ""): build_rule_score(movie, profile)
        for movie in movies
        if movie.get("id")
    }


def build_rule_signals_payload(
    movies: list[dict[str, Any]],
    rule_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Create a compact JSON file that explains deterministic bounds to the LLM."""
    serialized_movies = []
    for movie in movies:
        rule_info = rule_map.get(movie.get("id", ""), {})
        serialized_movies.append(
            {
                "movie_id": movie.get("id", ""),
                "title": movie.get("title", ""),
                "rule_score": rule_info.get("rule_score"),
                "recommendation_floor": rule_info.get("recommendation_floor"),
                "recommendation_ceiling": rule_info.get("recommendation_ceiling"),
                "metadata_confidence": rule_info.get("metadata_confidence"),
                "key_rule_matches": rule_info.get("key_rule_matches", []),
                "key_rule_penalties": rule_info.get("key_rule_penalties", []),
            }
        )

    return {
        "policy": {
            "name": "rules_first_v1",
            "summary": (
                "rule_score is the deterministic baseline. recommendation_floor is the minimum "
                "allowed label, recommendation_ceiling is the maximum allowed label. "
                "Use metadata_confidence to avoid overclaiming on sparse metadata."
            ),
        },
        "movies": serialized_movies,
    }


def compute_confidence(
    rule_info: dict[str, Any],
    analysis: dict[str, Any],
    llm_delta: int,
    final_recommendation: str,
) -> float:
    """Combine metadata richness, rule clarity, and LLM agreement into final confidence."""
    model_confidence = clamp(float(analysis.get("confidence", 0.65)), 0.0, 1.0)
    structural = 0.85 if rule_info.get("strong_positive") or rule_info.get("hard_negative") else 0.6
    confidence = (
        rule_info.get("metadata_confidence", 0.5) * 0.45
        + structural * 0.25
        + model_confidence * 0.30
    )
    confidence -= min(abs(llm_delta) / 40, 0.25)
    if final_recommendation == "must_see" and rule_info.get("recommendation_floor") != "must_see":
        confidence -= 0.08
    return round(clamp(confidence, 0.0, 1.0), 2)


def bounded_merge_analysis(
    movie: dict[str, Any],
    analysis: dict[str, Any],
    rule_info: dict[str, Any],
    thresholds: dict[str, int],
) -> dict[str, Any]:
    """Merge one LLM analysis with deterministic rule bounds."""
    rule_score = int(rule_info.get("rule_score", 50))
    llm_score_raw = analysis.get("relevance_score", rule_score)
    try:
        llm_score = int(round(float(llm_score_raw)))
    except (TypeError, ValueError):
        llm_score = rule_score
    llm_score = int(clamp(llm_score, 0, 100))

    delta_cap = 8 if rule_info.get("strong_positive") or rule_info.get("hard_negative") else 15
    bounded_delta = int(clamp(llm_score - rule_score, -delta_cap, delta_cap))
    final_score = int(clamp(rule_score + bounded_delta, 0, 100))

    llm_recommendation = analysis.get("recommendation")
    recommendation = recommendation_from_score(final_score, thresholds)
    if llm_recommendation in RECOMMENDATION_ORDER:
        recommendation = stronger_recommendation(recommendation, llm_recommendation)
    recommendation = apply_recommendation_bounds(
        recommendation,
        rule_info.get("recommendation_floor"),
        rule_info.get("recommendation_ceiling"),
    )
    final_score = fit_score_to_recommendation(final_score, recommendation, thresholds)

    confidence = compute_confidence(rule_info, analysis, bounded_delta, recommendation)
    review_required = False
    if confidence < 0.55:
        review_required = True
    if abs(bounded_delta) >= 12 and not rule_info.get("strong_positive"):
        review_required = True
    if (
        recommendation == "must_see"
        and confidence < 0.78
        and rule_info.get("recommendation_floor") != "must_see"
    ):
        review_required = True
    if (
        rule_info.get("metadata_confidence", 0.5) < 0.45
        and recommendation in {"must_see", "recommended"}
        and not rule_info.get("strong_positive")
    ):
        review_required = True

    if (
        review_required
        and recommendation == "must_see"
        and rule_info.get("recommendation_floor") != "must_see"
    ):
        recommendation = "recommended"
        final_score = fit_score_to_recommendation(final_score, recommendation, thresholds)

    reasoning = str(analysis.get("reasoning", "")).strip()
    key_matches = unique_strings(
        rule_info.get("key_rule_matches", [])
        + list(analysis.get("key_matches", []) or [])
    )
    red_flags = unique_strings(
        rule_info.get("key_rule_penalties", [])
        + list(analysis.get("red_flags", []) or [])
    )
    decision_basis = unique_strings(
        rule_info.get("decision_basis", [])
        + list(analysis.get("decision_basis", []) or [])
        + [f"rule_score:{rule_score}", f"llm_delta:{bounded_delta:+d}"]
        + (["quality:review_required"] if review_required else [])
    )

    return {
        "movie": {
            "id": movie.get("id", analysis.get("movie_id", "")),
            "title": movie.get("title", "Unknown"),
            "original_title": movie.get("original_title", ""),
            "director": movie.get("director", ""),
            "actors": movie.get("actors", []),
            "genres": movie.get("genres", []),
            "year": movie.get("year"),
            "duration_min": movie.get("duration_min"),
            "source": movie.get("source", ""),
            "url": movie.get("url", ""),
            "showtimes": movie.get("showtimes", []),
            "available_days": movie.get("available_days", []),
            "available_days_accurate": movie.get("available_days_accurate", []),
        },
        "relevance_score": final_score,
        "confidence": confidence,
        "recommendation": recommendation,
        "reasoning": reasoning,
        "key_matches": key_matches,
        "red_flags": red_flags,
        "rule_score": rule_score,
        "llm_delta": bounded_delta,
        "review_required": review_required,
        "decision_basis": decision_basis,
    }
