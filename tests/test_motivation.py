"""Tests for motivation phrase selection logic."""

import pytest

from bot.services.motivation import (
    ACTIVE_THRESHOLD,
    DAILY_THRESHOLD,
    LIGHTNING_THRESHOLD,
    PHRASES,
    get_category,
    get_phrase,
)


# ---------------------------------------------------------------------------
# get_category — deterministic logic tests
# ---------------------------------------------------------------------------

def _cat(**kwargs):
    """Call get_category with sensible defaults, overriding only what's needed."""
    defaults = dict(
        is_newcomer=False,
        is_veteran=False,
        weekly_karma=0,
        weekly_first_hour=0,
        weekly_first_day=0,
    )
    defaults.update(kwargs)
    return get_category(**defaults)


def test_newcomer_wins_over_everything():
    assert _cat(
        is_newcomer=True,
        is_veteran=True,
        weekly_karma=100,
        weekly_first_hour=10,
        weekly_first_day=10,
    ) == "newcomer"


def test_lightning_beats_daily_and_veteran():
    assert _cat(
        weekly_first_hour=LIGHTNING_THRESHOLD,
        weekly_first_day=DAILY_THRESHOLD,
        is_veteran=True,
        weekly_karma=ACTIVE_THRESHOLD,
    ) == "lightning"


def test_lightning_exact_threshold():
    assert _cat(weekly_first_hour=LIGHTNING_THRESHOLD) == "lightning"


def test_lightning_below_threshold_falls_to_next():
    assert _cat(weekly_first_hour=LIGHTNING_THRESHOLD - 1) != "lightning"


def test_daily_when_first_day_meets_threshold_and_first_hour_does_not():
    assert _cat(
        weekly_first_day=DAILY_THRESHOLD,
        weekly_first_hour=LIGHTNING_THRESHOLD - 1,
    ) == "daily"


def test_daily_exact_threshold():
    assert _cat(weekly_first_day=DAILY_THRESHOLD, weekly_first_hour=0) == "daily"


def test_daily_below_threshold_not_daily():
    assert _cat(weekly_first_day=DAILY_THRESHOLD - 1) != "daily"


def test_active_veteran_when_veteran_and_active():
    assert _cat(is_veteran=True, weekly_karma=ACTIVE_THRESHOLD) == "active_veteran"


def test_dormant_veteran_when_veteran_and_low_karma():
    assert _cat(is_veteran=True, weekly_karma=ACTIVE_THRESHOLD - 1) == "dormant_veteran"


def test_dormant_veteran_zero_karma():
    assert _cat(is_veteran=True, weekly_karma=0) == "dormant_veteran"


def test_active_non_veteran():
    assert _cat(is_veteran=False, weekly_karma=ACTIVE_THRESHOLD) == "active"


def test_active_beats_dormant_veteran_when_not_veteran():
    # weekly_karma >= threshold but not veteran → active, not dormant_veteran
    assert _cat(is_veteran=False, weekly_karma=ACTIVE_THRESHOLD) == "active"


def test_regular_fallback():
    assert _cat() == "regular"


def test_regular_when_all_below_thresholds():
    assert _cat(
        weekly_karma=ACTIVE_THRESHOLD - 1,
        weekly_first_day=DAILY_THRESHOLD - 1,
        weekly_first_hour=LIGHTNING_THRESHOLD - 1,
    ) == "regular"


# ---------------------------------------------------------------------------
# get_phrase — output validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lang", ["ru", "en"])
@pytest.mark.parametrize("category", [
    "newcomer", "lightning", "daily",
    "active_veteran", "dormant_veteran", "active", "regular",
])
def test_get_phrase_returns_non_empty_string(lang, category):
    phrase = get_phrase(category, lang)
    assert isinstance(phrase, str)
    assert len(phrase) > 0


def test_get_phrase_unknown_lang_falls_back_to_ru():
    phrase = get_phrase("newcomer", lang="zz")
    assert phrase in PHRASES["ru"]["newcomer"]


def test_get_phrase_unknown_category_falls_back_to_regular():
    phrase = get_phrase("nonexistent_category", lang="ru")  # type: ignore[arg-type]
    assert phrase in PHRASES["ru"]["regular"]


def test_each_category_has_ten_phrases_per_lang():
    for lang in ("ru", "en"):
        for category, phrases in PHRASES[lang].items():
            assert len(phrases) == 10, (
                f"Expected 10 phrases for {lang}/{category}, got {len(phrases)}"
            )


def test_get_phrase_randomness(monkeypatch):
    """Calling get_phrase multiple times should not always return the same phrase."""
    results = {get_phrase("regular", "ru") for _ in range(50)}
    assert len(results) > 1
