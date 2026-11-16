"""Game rules text shown in groups (/karma_on, /about_karma)."""

from bot.i18n import t


def build_rules_text(lang: str, post_cost: int) -> str:
    """Build the game rules message in the given language.

    Args:
        lang: Language code ('ru' or 'en')
        post_cost: Karma cost to post; a cost line is added when it is > 0

    Returns:
        Rules text ready to send
    """
    post_cost_line = ""
    if post_cost > 0:
        post_cost_line = t("rules_post_cost", lang=lang, cost=post_cost) + "\n\n"
    return t("rules_text", lang=lang, post_cost_line=post_cost_line).strip()
