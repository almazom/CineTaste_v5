"""
Test ct-fetch tool contract validation.
"""

import json
import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "_shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "ct-fetch"))

from validate import validate_against_contract
from adapter_kinoteatr import (
    DOTENV_PATH,
    _build_listing_url,
    _extract_detail_metadata,
    _fetch_html,
    fetch_movies,
    fetch_movies_month,
    parse_html,
    parse_html_with_date,
)


class TestKinoteatrAdapter:
    """Test kinoteatr.ru adapter."""

    @pytest.mark.network
    def test_fetch_movies_returns_list(self):
        """Should return a list of movies."""
        movies = fetch_movies("naberezhnie-chelni")
        assert isinstance(movies, list)
        assert len(movies) > 0

    @pytest.mark.network
    def test_movie_has_required_fields(self):
        """Each movie should have required fields."""
        movies = fetch_movies("naberezhnie-chelni")
        for movie in movies[:5]:  # Check first 5
            assert "id" in movie
            assert "title" in movie
            assert "source" in movie
            assert movie["source"] == "kinoteatr.ru"

    @pytest.mark.network
    def test_movie_titles_not_empty(self):
        """Movie titles should not be empty."""
        movies = fetch_movies("naberezhnie-chelni")
        for movie in movies:
            assert movie["title"], f"Empty title for movie {movie['id']}"

    @pytest.mark.network
    def test_movie_urls_valid(self):
        """Movie URLs should be valid."""
        movies = fetch_movies("naberezhnie-chelni")
        for movie in movies:
            if movie.get("url"):
                assert movie["url"].startswith("https://kinoteatr.ru/film/")

    def test_invalid_city_raises_error(self):
        """Invalid city should raise ValueError."""
        with pytest.raises(ValueError):
            fetch_movies("invalid-city-name")


class TestFetchDeterministic:
    """Deterministic unit tests for parser/fetch behavior."""

    @staticmethod
    def sample_html() -> str:
        fixture = Path(__file__).parent / "fixtures" / "kinoteatr_sample.html"
        return fixture.read_text(encoding="utf-8")

    def test_parse_html_extracts_movies(self):
        movies = parse_html(self.sample_html())
        assert len(movies) == 2
        assert movies[0]["title"] == "Фильм Один"
        assert movies[1]["title"] == "Фильм Два"
        assert movies[0]["url"].startswith("https://kinoteatr.ru/film/")
        assert "триллер" in movies[0]["genres"]

    def test_parse_html_skips_promo_cards(self):
        movies = parse_html(self.sample_html())
        titles = {m["title"] for m in movies}
        assert "Подарочный сертификат" not in titles

    def test_fetch_movies_appends_when_query(self, monkeypatch):
        response = Mock()
        response.text = self.sample_html()
        response.raise_for_status = Mock()

        captured = {"urls": []}

        def fake_get(url, **kwargs):
            captured["urls"].append(url)
            return response

        monkeypatch.setattr("adapter_kinoteatr.requests.get", fake_get)
        movies = fetch_movies("naberezhnie-chelni", "2026-03-10")

        assert "when=2026-03-10" in captured["urls"][0]
        assert len(movies) == 2

    def test_fetch_movies_month_hits_30_listing_days(self, monkeypatch):
        captured_dates = []

        def fake_fetch_html(url, headers, timeout=30, attempts=3):
            match = url.split("when=")[-1]
            captured_dates.append(match)
            return self.sample_html()

        monkeypatch.setattr("adapter_kinoteatr._fetch_html", fake_fetch_html)
        monkeypatch.setattr("adapter_kinoteatr._enrich_from_detail_pages", lambda movies: None)

        movies = fetch_movies_month("naberezhnie-chelni")

        assert len(captured_dates) == 30
        assert len(movies) == 2

    def test_build_listing_url_normalizes_env_query(self):
        url = _build_listing_url("naberezhnie-chelni", "2026-03-10")
        assert url == "https://kinoteatr.ru/kinoafisha/naberezhnie-chelni/?when=2026-03-10"

    def test_fetch_html_retries_retryable_status(self, monkeypatch):
        response_502 = Mock(status_code=502, text="<title>Error 502</title>", headers={"server": "ddos-guard"})
        response_502.raise_for_status = Mock()
        response_200 = Mock(status_code=200, text="<html>ok</html>", headers={"server": "ok"})
        response_200.raise_for_status = Mock()
        calls = {"count": 0}

        def fake_get(url, headers, timeout):
            calls["count"] += 1
            return response_502 if calls["count"] < 3 else response_200

        monkeypatch.setattr("adapter_kinoteatr.requests.get", fake_get)
        monkeypatch.setattr("adapter_kinoteatr.time.sleep", lambda *_: None)

        html = _fetch_html("https://kinoteatr.ru/test", headers={"User-Agent": "x"}, attempts=3)

        assert html == "<html>ok</html>"
        assert calls["count"] == 3

    def test_fetch_movies_request_exception(self, monkeypatch):
        # Use requests.RequestException branch via real class path.
        import requests
        def fake_get_requests(url, headers, timeout):
            raise requests.RequestException("network fail")

        monkeypatch.setattr("adapter_kinoteatr.requests.get", fake_get_requests)

        with pytest.raises(ConnectionError):
            fetch_movies("naberezhnie-chelni")

    def test_parse_html_missing_anchor_keeps_url_missing(self):
        html = """
        <div data-gtm-list-item-filmName="Без ссылки" data-gtm-list-item-genre="драма"></div>
        <span class="contentRating">16+</span>
        """
        movies = parse_html(html)
        assert len(movies) == 1
        assert "url" not in movies[0]

    def test_parse_html_matches_yo_title_variant(self, monkeypatch):
        html = """
        <div data-gtm-list-item-filmName="О моем перерождении в слизь: Слезы Синего моря" data-gtm-list-item-genre="аниме, фэнтези"></div>
        <span class="contentRating">16+</span>
        <a href="https://kinoteatr.ru/film/o-moem-pererozhdenii-v-sliz-slezy-sinego-morya/naberezhnie-chelni/" data-gtm-ec-name="О моем перерождении в слизь: Слёзы Синего моря"></a>
        """
        monkeypatch.setattr("adapter_kinoteatr._enrich_from_detail_pages", lambda movies: None)
        movies = parse_html(html)
        assert movies[0]["url"].endswith("/film/o-moem-pererozhdenii-v-sliz-slezy-sinego-morya/naberezhnie-chelni/")

    def test_parse_html_with_date_matches_yo_title_variant(self, monkeypatch):
        html = """
        <div data-gtm-list-item-filmName="О моем перерождении в слизь: Слезы Синего моря" data-gtm-list-item-genre="аниме, фэнтези"></div>
        <span class="contentRating">16+</span>
        <a href="https://kinoteatr.ru/film/o-moem-pererozhdenii-v-sliz-slezy-sinego-morya/naberezhnie-chelni/" data-gtm-ec-name="О моем перерождении в слизь: Слёзы Синего моря"></a>
        """
        monkeypatch.setattr("adapter_kinoteatr._enrich_from_detail_pages", lambda movies: None)
        movies = parse_html_with_date(html, "2026-04-26")
        assert movies[0]["url"].endswith("/film/o-moem-pererozhdenii-v-sliz-slezy-sinego-morya/naberezhnie-chelni/")
        assert movies[0]["available_days"] == ["2026-04-26"]

    def test_extract_detail_metadata_recovers_description_duration_and_year(self):
        html = """
        <meta name="description" content="Фильм «Лабиринт» (2026): цены на билеты." />
        <h1 itemprop="name">Лабиринт</h1>
        <meta itemprop="duration" content="T115M" />
        <p itemprop="description">
            Застенчивая старшеклассница Сиори Маэдзава попадает в таинственный мир.
        </p>
        <span class="clear_span" itemprop="director" itemscope itemtype="http://schema.org/Person">
            <span class="clear_span" itemprop="name">Сё\u200cдзи Кавамо\u200cри</span>
        </span>
        <div class="movie_actors">В ролях<td><span itemprop="name">Актёр Один</span></td></div>
        <div data-dates="2026-04-26, 2026-04-27"></div>
        """

        metadata = _extract_detail_metadata(html)

        assert metadata["director"] == "Сёдзи Кавамори"
        assert metadata["duration_min"] == 115
        assert metadata["year"] == 2026
        assert metadata["raw_description"].startswith("Застенчивая старшеклассница")
        assert metadata["actors"] == ["Актёр Один"]
        assert metadata["available_days_accurate"] == ["2026-04-26", "2026-04-27"]

    def test_extract_detail_metadata_prefers_page_genres(self):
        html = """
        <span itemprop="genre">Аниме</span>, <span itemprop="genre"> Мультфильм</span>,
        <span itemprop="genre"> Семейный</span>
        """

        metadata = _extract_detail_metadata(html)

        assert metadata["genres"] == ["Аниме", "Мультфильм", "Семейный"]

    def test_dotenv_path_is_project_relative(self):
        expected = (Path(__file__).resolve().parents[1] / ".env").resolve()
        assert DOTENV_PATH.resolve() == expected


class TestMovieBatchContract:
    """Test movie-batch contract validation."""

    def test_sample_valid(self):
        """Sample file should validate."""
        sample_path = Path(__file__).parent.parent / "contracts" / "examples" / "movie-batch.sample.json"
        with open(sample_path) as f:
            data = json.load(f)
        is_valid, errors = validate_against_contract(data, "movie-batch")
        assert is_valid, f"Validation errors: {errors}"

    def test_missing_movies_field(self):
        """Missing movies field should fail."""
        data = {"meta": {"city": "test"}}
        is_valid, errors = validate_against_contract(data, "movie-batch")
        assert not is_valid

    def test_missing_meta_field(self):
        """Missing meta field should fail."""
        data = {"movies": []}
        is_valid, errors = validate_against_contract(data, "movie-batch")
        assert not is_valid


class TestFetchIntegration:
    """Integration tests for ct-fetch."""

    @pytest.mark.network
    def test_full_fetch_produces_valid_contract(self):
        """Full fetch should produce valid movie-batch."""
        movies = fetch_movies("naberezhnie-chelni")
        data = {
            "movies": movies,
            "meta": {
                "city": "naberezhnie-chelni",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "fetched_at": datetime.now().isoformat()
            }
        }

        is_valid, errors = validate_against_contract(data, "movie-batch")
        assert is_valid, f"Validation errors: {errors}"
