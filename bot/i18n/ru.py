"""Russian translations for LinkedIn Karma Bot.

This module contains all Russian language strings used throughout the bot.
"""

translations = {
    # User status and karma messages
    "asks_support": "просит поддержки",
    "per_week": "За неделю",
    "support": "Поддержка",
    "posts": "Постов",
    "newcomer": "новичок",
    "veteran": "ветеран",
    "your_karma": "Ваша карма",
    "weekly": "за неделю",
    "total": "всего",

    # Leaderboard messages
    "top_weekly": "Топ по поддержке за неделю",
    "top_all": "Топ по поддержке за всё время",
    "no_data": "Пока нет данных",

    # Statistics
    "stats_title": "Статистика группы",
    "total_users": "Всего участников",
    "total_posts": "Всего постов",
    "total_reactions": "Всего реакций",
    "weekly_posts": "Постов за неделю",
    "weekly_reactions": "Реакций за неделю",

    # Commands help
    "help_text": """
Привет! Я бот для подсчёта кармы за публикации в LinkedIn.

Как это работает:
1. Поделитесь ссылкой на свой пост в LinkedIn
2. Другие участники отреагируют на ваше сообщение
3. Вы получите карму за их поддержку

Доступные команды:
/start - Начать работу с ботом
/help - Показать эту справку
/karma - Посмотреть свою карму
/top - Топ участников за неделю
/top_all - Топ участников за всё время
/stats - Статистика группы

Команды для администраторов:
/set_language <ru|en> - Установить язык группы
/set_karma_period <дни> - Установить период подсчёта кармы
/set_veteran_threshold <число> - Установить порог для статуса ветерана
/set_post_cost <число> - Установить стоимость поста в очках кармы
/reset_karma @username - Сбросить карму пользователя
/export - Выгрузить статистику в CSV

Система рейтинга:
⭐ - 1-2 очка кармы
⭐⭐ - 3-5 очков
⭐⭐⭐ - 6-10 очков
⭐⭐⭐⭐ - 11-20 очков
⭐⭐⭐⭐⭐ - 21+ очков

Поддерживаемые ссылки:
- linkedin.com/posts/...
- linkedin.com/feed/update/...
- linkedin.com/pulse/...

Удачи в наборе кармы!
""",

    # Admin messages
    "admin_only": "Эта команда доступна только для администраторов",
    "setting_updated": "Настройка обновлена",
    "invalid_value": "Неверное значение",
    "language_set": "Язык группы установлен: {value}",
    "karma_period_set": "Период подсчёта кармы установлен: {value} дней",
    "veteran_threshold_set": "Порог для ветерана установлен: {value} очков",
    "post_cost_set": "Стоимость поста установлена: {value} очков",

    # Post messages
    "post_registered": "Пост зарегистрирован!",
    "post_already_registered": "Этот пост уже зарегистрирован",
    "first_post": "Поздравляем с первым постом!",
    "not_enough_karma": "Недостаточно кармы для публикации. Нужно: {required}, у вас: {current}",
    "post_newcomer": "📝 {username} 🌱 (впервые) просит поддержки\nЗа {period} дней - Поддержал других: {karma}\nПопросил поддержки: {posts}",
    "post_veteran": "📝 {username} 🎖️ ({total_karma}) просит поддержки\nЗа {period} дней - Поддержал других: {karma}\nПопросил поддержки: {posts}",
    "post_regular": "📝 {username} просит поддержки\nЗа {period} дней - Поддержал других: {karma}\nПопросил поддержки: {posts}",

    # Reaction messages
    "reaction_added": "Поддержка засчитана!",
    "cannot_react_own": "Нельзя реагировать на свой собственный пост",
    "already_reacted": "Вы уже поддержали этот пост",

    # Error messages
    "error_occurred": "Произошла ошибка. Попробуйте позже.",
    "no_linkedin_url": "Сообщение не содержит ссылку на LinkedIn",
    "user_not_found": "Пользователь не найден",
    "group_only_command": "Эта команда работает только в группах. Используйте её в группе, где работает бот.",

    # Welcome message
    "welcome": """
Добро пожаловать в группу!

Этот бот помогает участникам поддерживать друг друга, отмечая публикации в LinkedIn.

Чтобы узнать больше, используйте команду /help
""",
    "commands_list": """
Доступные команды:
/start - Начать работу с ботом
/help - Показать справку
/karma - Посмотреть свою карму
/top - Топ участников за неделю
/top_all - Топ участников за всё время
/stats - Статистика группы
""",

    # Misc
    "position": "№",
    "points": "очков",
    "user": "пользователь",
    "deleted_user": "удалённый пользователь",
}
