"""
Test ct-format tool contract validation.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "_shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "ct-format"))

from validate import validate_against_contract
from adapter_telegram import render_message, render_movie_line, render_detailed


def make_filtered_item(
    movie_id: str = "1",
    title: str = "Test Movie",
    url: str | None = "https://example.com",
    score: int = 85,
    recommendation: str = "recommended",
    **movie_overrides
) -> dict:
    """Create a minimal filtered item for renderer tests."""
    movie = {"id": movie_id, "title": title}
    if url is not None:
        movie["url"] = url
    movie.update(movie_overrides)
    return {
        "movie": movie,
        "relevance_score": score,
        "recommendation": recommendation
    }


class TestTelegramRenderer:
    """Test Telegram markdown rendering."""

    def test_render_message_basic(self):
        """Should render basic message."""
        filtered = [make_filtered_item()]
        message = render_message(filtered, "Test City")

        assert "Test Movie" in message
        assert "📊" not in message
        assert "📍" not in message

    def test_render_message_must_see(self):
        """Should render must_see section."""
        filtered = [make_filtered_item(title="Must See", score=95, recommendation="must_see")]
        message = render_message(filtered, "Test City")

        assert "ОБЯЗАТЕЛЬНО" in message

    def test_render_movie_line(self):
        """Should render movie line with markdown."""
        item = make_filtered_item(title="Test")
        line = render_movie_line(item, 1)

        assert "Test" in line
        assert "85%" in line
        assert "https://example.com" in line

    def test_render_movie_line_without_url(self):
        """Should render plain title when URL is missing."""
        item = make_filtered_item(title="Test", url=None, score=70)
        line = render_movie_line(item, 2)
        assert "Test" in line
        assert "https://" not in line

    def test_render_movie_line_over_20_index(self):
        """Should fallback to numeric prefix for large indexes."""
        item = make_filtered_item(title="Test", url=None, score=70)
        line = render_movie_line(item, 21)
        assert line.startswith("21.")

    def test_render_message_with_explicit_date(self):
        """Should use provided date instead of current date."""
        filtered = []
        message = render_message(filtered, "Test City", date="10.03.2026")
        assert "10.03.2026" in message
        assert "Сегодня ничего не подходит" in message
        assert "В ближайшие 7 дней ничего не подходит" in message
        assert "В ближайшие 30 дней ничего не подходит" in message

    def test_render_message_with_same_price_showtimes(self):
        filtered = [
            make_filtered_item(
                title="Сеансы",
                showtimes=[
                    {
                        "time": "14:25",
                        "datetime_iso": "2026-03-10T14:25:00+03:00",
                        "price": "от 250 ₽",
                    },
                    {
                        "time": "17:30",
                        "datetime_iso": "2026-03-10T17:30:00+03:00",
                        "price": "от 250 ₽",
                    },
                ],
            )
        ]
        message = render_message(filtered, "Test City")
        assert "14:25, 17:30, от 250 ₽" in message
        assert "🕒" not in message
        assert "💳" not in message

    def test_render_message_splits_week_and_month_horizons(self):
        today = datetime.now().date()
        filtered = [
            make_filtered_item(
                title="Сегодня",
                showtimes=[
                    {
                        "time": "14:25",
                        "datetime_iso": f"{today.isoformat()}T14:25:00+03:00",
                        "price": "от 250 ₽",
                    }
                ],
                available_days_accurate=[today.isoformat()],
                recommendation="must_see",
                score=92,
            ),
            make_filtered_item(
                title="Неделя",
                available_days_accurate=[(today + timedelta(days=3)).isoformat()],
                recommendation="recommended",
                score=70,
            ),
            make_filtered_item(
                title="Месяц",
                available_days_accurate=[(today + timedelta(days=18)).isoformat()],
                recommendation="recommended",
                score=68,
            ),
        ]
        message = render_message(filtered, "Test City")

        assert "┏━━ СЕГОДНЯ ━━┓" in message
        assert "┏━━ В БЛИЖАЙШИЕ 7 ДНЕЙ ━━┓" in message
        assert "┏━━ В БЛИЖАЙШИЕ 30 ДНЕЙ ━━┓" in message
        assert "Сегодня" in message
        assert "Неделя" in message
        assert "Месяц" in message
        assert "⏳ через 3 дня" in message
        assert "⏳ через 18 дней" in message

    def test_render_message_prefers_week_bucket_when_movie_has_week_and_month_dates(self):
        today = datetime.now().date()
        filtered = [
            make_filtered_item(
                title="Смешанный горизонт",
                available_days_accurate=[
                    (today + timedelta(days=2)).isoformat(),
                    (today + timedelta(days=12)).isoformat(),
                ],
            )
        ]
        message = render_message(filtered, "Test City")

        assert "┏━━ В БЛИЖАЙШИЕ 7 ДНЕЙ ━━┓" in message
        assert "Смешанный горизонт" in message
        assert "┏━━ В БЛИЖАЙШИЕ 30 ДНЕЙ ━━┓" not in message or message.index("Смешанный горизонт") < message.index("┏━━ В БЛИЖАЙШИЕ 30 ДНЕЙ ━━┓")
        assert "⏳ послезавтра" in message

    def test_render_message_uses_week_phrase_for_seven_days(self):
        today = datetime.now().date()
        filtered = [
            make_filtered_item(
                title="Через неделю",
                available_days_accurate=[(today + timedelta(days=7)).isoformat()],
                recommendation="recommended",
                score=70,
            )
        ]

        message = render_message(filtered, "Test City")

        assert "⏳ через неделю" in message

    def test_render_message_uses_week_phrase_for_two_weeks(self):
        today = datetime.now().date()
        filtered = [
            make_filtered_item(
                title="Через две недели",
                available_days_accurate=[(today + timedelta(days=14)).isoformat()],
                recommendation="recommended",
                score=70,
            )
        ]

        message = render_message(filtered, "Test City")

        assert "⏳ через 2 недели" in message

    def test_render_message_with_different_prices_showtimes(self):
        filtered = [
            make_filtered_item(
                title="Сеансы",
                showtimes=[
                    {
                        "time": "09:10",
                        "datetime_iso": "2026-03-10T09:10:00+03:00",
                        "price": "от 165 ₽",
                    },
                    {
                        "time": "17:10",
                        "datetime_iso": "2026-03-10T17:10:00+03:00",
                        "price": "от 255 ₽",
                    },
                ],
            )
        ]
        message = render_message(filtered, "Test City")
        assert "09:10, от 165 ₽" in message
        assert "17:10, от 255 ₽" in message
        assert "🕒" not in message
        assert "💳" not in message

    def test_render_detailed(self):
        """Detailed renderer should include optional fields."""
        item = {
            "movie": {
                "id": "1",
                "title": "Detailed Movie",
                "director": "Director",
                "genres": ["drama"]
            },
            "relevance_score": 90,
            "reasoning": "Strong match"
        }
        text = render_detailed(item)
        assert "Detailed Movie" in text
        assert "Director" in text
        assert "Strong match" in text

    def test_render_empty_filtered(self):
        """Should handle empty filtered list."""
        message = render_message([], "Test City")
        assert "Сегодня ничего не подходит" in message
        assert "В ближайшие 7 дней ничего не подходит" in message
        assert "В ближайшие 30 дней ничего не подходит" in message
        assert "📊" not in message
        assert "📍" not in message

    def test_render_message_keeps_empty_week_section_visible(self):
        today = datetime.now().date()
        filtered = [
            make_filtered_item(
                title="Только месяц",
                available_days_accurate=[(today + timedelta(days=18)).isoformat()],
                recommendation="recommended",
                score=68,
            )
        ]

        message = render_message(filtered, "Test City")

        assert "┏━━ В БЛИЖАЙШИЕ 7 ДНЕЙ ━━┓" in message
        assert "В ближайшие 7 дней ничего не подходит" in message
        assert "┏━━ В БЛИЖАЙШИЕ 30 ДНЕЙ ━━┓" in message
        assert "Только месяц" in message


class TestMessageTextContract:
    """Test message-text contract validation."""

    def test_sample_valid(self):
        """Sample file should validate."""
        sample_path = Path(__file__).parent.parent / "contracts" / "examples" / "message-text.sample.json"
        with open(sample_path) as f:
            data = json.load(f)
        is_valid, errors = validate_against_contract(data, "message-text")
        assert is_valid, f"Validation errors: {errors}"

    def test_missing_text_field(self):
        """Missing text field should fail."""
        data = {"meta": {"template": "telegram", "formatted_at": "2026-03-02T00:00:00"}}
        is_valid, errors = validate_against_contract(data, "message-text")
        assert not is_valid

    def test_text_must_be_string(self):
        """Text must be a string type."""
        data = {
            "text": 123,  # Not a string
            "meta": {"template": "telegram", "formatted_at": "2026-03-02T00:00:00"}
        }
        is_valid, errors = validate_against_contract(data, "message-text")
        assert not is_valid


class TestFormatIntegration:
    """Integration tests for ct-format."""

    def test_full_format_produces_valid_contract(self):
        """Full format should produce valid message-text."""
        from datetime import datetime, timezone

        filtered = [make_filtered_item()]

        text = render_message(filtered, "Test City")

        data = {
            "text": text,
            "meta": {
                "template": "telegram",
                "city_display": "Test City",
                "movie_count": 1,
                "formatted_at": datetime.now(timezone.utc).isoformat()
            }
        }

        is_valid, errors = validate_against_contract(data, "message-text")
        assert is_valid, f"Validation errors: {errors}"
