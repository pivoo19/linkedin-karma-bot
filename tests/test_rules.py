"""Tests for the game rules text."""

from bot.i18n import t
from bot.services.rules import build_rules_text


def test_rules_starts_with_title():
    assert build_rules_text("ru", 0).strip().startswith("🎮 Правила игры")


def test_rules_has_no_command_list():
    for lang in ("ru", "en"):
        text = build_rules_text(lang, 0)
        for command in ("/karma", "/top", "/help"):
            assert command not in text


def test_rules_no_cost_line_when_free():
    text = build_rules_text("ru", 0)
    assert "Публикация поста стоит" not in text
    assert "\n\n\n" not in text


def test_rules_cost_line_when_paid():
    text = build_rules_text("ru", 3)
    assert "Публикация поста стоит 3 очков кармы." in text
    assert text.index("Публикация поста стоит") < text.index("🔔")
    assert "\n\n\n" not in text


def test_rules_en_available():
    assert build_rules_text("en", 0).strip().startswith("🎮 Game rules")


def test_help_lists_new_commands():
    for lang in ("ru", "en"):
        help_text = t("help_text", lang=lang)
        for command in ("/about_karma", "/karma_on", "/karma_off", "/karma_topics"):
            assert command in help_text
