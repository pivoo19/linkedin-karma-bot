"""Motivation phrases appended to post notifications.

Selects a short call-to-action phrase based on the poster's karma profile.
"""

import random
from typing import Literal

Category = Literal[
    "newcomer",
    "lightning",
    "daily",
    "active_veteran",
    "dormant_veteran",
    "active",
    "regular",
]

PHRASES: dict[str, dict[Category, list[str]]] = {
    "ru": {
        "newcomer": [
            "Первый пост — поддержим новичка с самого начала!",
            "Только вступил в игру — давайте покажем, как здесь принято!",
            "Первый шаг уже сделан — поддержим в начале пути!",
            "Новенький в группе — встретим тепло!",
            "Первый пост в группе — самое время показать, что здесь рады новым!",
            "Начинает с нуля — поддержим, чтобы не начинал в одиночку!",
            "Первый раз решился поделиться — не оставим без внимания!",
            "Новичок делает первый шаг — протянем руку помощи!",
            "Дебют в группе — поддержим, чтобы захотел вернуться!",
            "Только начинает — ваша поддержка сейчас важнее всего!",
        ],
        "lightning": [
            "Помогает всем в первый час — поддержим без промедления!",
            "Первым реагирует на чужие посты — ответим тем же!",
            "Молниеносно помогает другим — покажем, что это ценят!",
            "Пока другие думают, он уже поставил лайк — поддержим в ответ!",
            "Самый быстрый в поддержке — грех тянуть с ответом!",
            "Реагирует в первый час — давайте и мы не опоздаем!",
            "Скорость его поддержки — пример для всех. Поддержим!",
            "Не ждёт, пока попросят — помогает сразу. Ответим взаимностью!",
            "Всегда в первых рядах, когда нужна помощь — не оставим его ждать!",
            "Быстрее всех приходит на помощь — поддержим так же быстро!",
        ],
        "daily": [
            "Сам помогает в первый день — поддержите и вы!",
            "Не откладывает поддержку другим — давайте ответим тем же!",
            "Помогает пока пост горячий — поддержим его в ответ!",
            "Всегда успевает в первый день — грех оставить без поддержки!",
            "Реагирует быстро на чужие посты — покажем, что это ценят!",
            "День не проходит без его поддержки — поддержим и мы!",
            "Откликается в первый день — ответим тем же!",
            "Помогает пока пост на виду — не упустим момент!",
            "Всегда находит время помочь в первый день — найдём и мы!",
            "Первый день — и уже готов помочь. Поддержим в ответ!",
        ],
        "active_veteran": [
            "Ветеран, который не останавливается — грех не ответить!",
            "Годами помогает и не сбавляет темп — поддержим в ответ!",
            "Столько помог группе и продолжает — это заслуживает поддержки!",
            "Один из самых активных за всё время — и до сих пор в строю!",
            "Ветеран на активе — такую преданность надо поддерживать!",
            "Никогда не бросал группу — не бросим и мы его!",
            "Помогал раньше, помогает сейчас — поддержим без раздумий!",
            "Карма заработана делами, а не словами — ответим тем же!",
            "Самый преданный участник группы — заслуживает поддержки!",
            "Активен всегда — это редкость. Поддержим такого человека!",
        ],
        "dormant_veteran": [
            "Раньше поддерживал всех подряд — настало время вернуть долг!",
            "Помог десяткам в этой группе — поддержим и мы его!",
            "Один из первых, кто помогал здесь — не забудем об этом!",
            "Заложил традицию поддержки в группе — ответим тем же!",
            "Его карма говорит сама за себя — поддержите без раздумий!",
            "Столько поддержки отдал — пора получить обратно!",
            "Ветеран группы просит помощи — не оставим без ответа!",
            "Когда-то помогал каждому — теперь очередь помочь ему!",
            "За плечами — сотни лайков другим. Поддержим в ответ!",
            "Свою карму заработал честно — давайте не подведём!",
        ],
        "active": [
            "Активно помогает другим — поддержим в ответ!",
            "Не жалеет времени на поддержку — ответим взаимностью!",
            "Один из самых активных в группе прямо сейчас — поддержим!",
            "Помогает всем вокруг — давайте поможем и ему!",
            "Его поддержка работает в обе стороны — покажем это!",
            "Активен и щедр на поддержку — заслуживает того же!",
            "Не скупится на лайки другим — не поскупимся и мы!",
            "Поддерживает группу делом — поддержим и его!",
            "Карму не прячет — помогает активно. Ответим тем же!",
            "Из тех, кто реально помогает — это ценно. Поддержим!",
        ],
        "regular": [
            "Поддержите — и он ответит взаимностью!",
            "Каждый лайк важен — давайте поможем!",
            "Поддержка — это то, что держит группу вместе!",
            "Помогите сегодня — завтра помогут вам!",
            "Один лайк от каждого — и пост взлетит!",
            "Поддержим друг друга — в этом смысл группы!",
            "Не проходите мимо — поддержите пост!",
            "Вместе мы сильнее — поддержим в ответ!",
            "Ваш лайк важен — не откладывайте!",
            "Поддержка всегда возвращается — начните прямо сейчас!",
        ],
    },
    "en": {
        "newcomer": [
            "First post here — let's give them a warm welcome!",
            "Just getting started — show them how we do it!",
            "First step taken — let's support them from day one!",
            "Brand new to the group — let's make them feel at home!",
            "Their first post — don't let it go unnoticed!",
            "Starting from zero — let's make sure they don't start alone!",
            "First time sharing — let's show them it's worth it!",
            "A newcomer has arrived — let's reach out!",
            "Debut post — support them so they come back!",
            "Just beginning — your support matters most right now!",
        ],
        "lightning": [
            "Always helps within the first hour — let's return the favor!",
            "First to react to others' posts — let's do the same!",
            "Lightning-fast support — let's show that it's appreciated!",
            "Likes before anyone else — let's support them back!",
            "The fastest supporter in the group — don't be late to respond!",
            "Reacts within the first hour — let's not keep them waiting!",
            "Their speed of support is an example for all — let's show up!",
            "Doesn't wait to be asked — helps right away. Let's return the favor!",
            "Always first when help is needed — let's not make them wait!",
            "Fastest to show up for others — let's be just as quick!",
        ],
        "daily": [
            "Helps others on day one — let's do the same!",
            "Never delays support — let's return the favor!",
            "Helps while the post is still hot — let's support them back!",
            "Always there on the first day — too good to leave without support!",
            "Quick to react to others — let's show that it's valued!",
            "A day never passes without their support — let's respond in kind!",
            "Responds on day one — let's do the same!",
            "Helps while the post is still visible — let's not miss the moment!",
            "Always finds time to help on day one — let's find time too!",
            "Day-one support is their signature — let's reply in kind!",
        ],
        "active_veteran": [
            "A veteran who never slows down — let's return the favor!",
            "Helping for years without stopping — let's support them back!",
            "Done so much for the group and keeps going — they deserve support!",
            "One of the most active all-time — and still going strong!",
            "A veteran still on active duty — loyalty like this deserves support!",
            "Never abandoned the group — let's not abandon them!",
            "Was helping before, still helping now — support without hesitation!",
            "Karma earned through action, not words — let's respond the same way!",
            "The most dedicated member in the group — they deserve our support!",
            "Always active — that's rare. Let's support this person!",
        ],
        "dormant_veteran": [
            "Used to support everyone here — time to pay it back!",
            "Helped dozens in this group — let's support them too!",
            "One of the first to help here — let's not forget that!",
            "Set the tone for support in this group — let's respond in kind!",
            "Their karma speaks for itself — support without hesitation!",
            "Gave so much support — it's time to give back!",
            "A group veteran asking for help — let's not leave them hanging!",
            "Used to help everyone — now it's our turn!",
            "Hundreds of likes given to others — let's return the favor!",
            "Earned their karma honestly — let's not let them down!",
        ],
        "active": [
            "Actively supporting others — let's support them back!",
            "Generous with their support — let's return the favor!",
            "One of the most active right now — let's show up!",
            "Helps everyone around — let's help them too!",
            "Support goes both ways — let's show it!",
            "Active and generous — they deserve the same!",
            "Never stingy with likes — let's be just as generous!",
            "Supports the group in action — let's support them!",
            "Karma in practice, not just words — let's respond in kind!",
            "One of those who really helps — that's rare. Let's support them!",
        ],
        "regular": [
            "Support them — and they'll return the favor!",
            "Every like counts — let's help!",
            "Support is what keeps this group together!",
            "Help today — get help tomorrow!",
            "One like from each of us — and this post will soar!",
            "Let's support each other — that's what this group is for!",
            "Don't scroll past — support the post!",
            "Together we're stronger — let's support them!",
            "Your like matters — don't put it off!",
            "Support always comes back around — start right now!",
        ],
    },
}

# Thresholds for category detection
LIGHTNING_THRESHOLD = 2   # weekly first-hour reactions
DAILY_THRESHOLD = 3       # weekly first-day reactions
ACTIVE_THRESHOLD = 5      # weekly karma


def get_category(
    *,
    is_newcomer: bool,
    is_veteran: bool,
    weekly_karma: int,
    weekly_first_hour: int,
    weekly_first_day: int,
) -> Category:
    """Determine motivation category based on user's karma profile.

    Priority (first match wins):
    1. newcomer      — first post ever
    2. lightning     — weekly_first_hour >= LIGHTNING_THRESHOLD
    3. daily         — weekly_first_day >= DAILY_THRESHOLD (but not lightning)
    4. active_veteran — veteran + weekly_karma >= ACTIVE_THRESHOLD
    5. dormant_veteran — veteran + weekly_karma < ACTIVE_THRESHOLD
    6. active        — weekly_karma >= ACTIVE_THRESHOLD (not veteran)
    7. regular       — fallback
    """
    if is_newcomer:
        return "newcomer"
    if weekly_first_hour >= LIGHTNING_THRESHOLD:
        return "lightning"
    if weekly_first_day >= DAILY_THRESHOLD:
        return "daily"
    if is_veteran and weekly_karma >= ACTIVE_THRESHOLD:
        return "active_veteran"
    if is_veteran:
        return "dormant_veteran"
    if weekly_karma >= ACTIVE_THRESHOLD:
        return "active"
    return "regular"


def get_phrase(category: Category, lang: str = "ru") -> str:
    """Return a random motivation phrase for the given category and language."""
    lang_phrases = PHRASES.get(lang, PHRASES["ru"])
    phrases = lang_phrases.get(category, lang_phrases["regular"])
    return random.choice(phrases)
