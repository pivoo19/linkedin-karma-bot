# Karma topics: bot works only in selected forum topics

## Why
In supergroups with topics (forums) the bot currently reacts in every topic. Group admins
want the bot to register posts, award karma and answer commands only in the topics they choose.

## Behaviour
- **Forum supergroups** (`chat.is_forum == True`): every topic is OFF by default.
  The bot ignores LinkedIn links and group commands in OFF topics, without any reply.
- **Regular groups and supergroups without topics**: unchanged. No enabling is needed.
- **Private chats** (`/start`, `/help`, `/reach`, callbacks): unchanged.
- Reactions need no filter. Telegram reaction updates carry no topic, and karma is awarded
  only for registered posts, which can now appear only in enabled topics.

## Admin commands (group admins only, reuse `is_admin`)
- `/karma_on`: enable the current topic. The bot then posts the "enabled" line and the rules message in that topic.
  Sending it in an already enabled topic just repeats the rules.
- `/karma_off`: disable the current topic. The bot sends a short confirmation.
- `/karma_topics`: list the enabled topics.
- All three work in any topic, including disabled ones. Non-admins get the existing `admin_only` reply.
- Outside a forum they reply that the command works only in groups with topics.
- The "General" topic can be enabled. Its messages have no `message_thread_id`, so it is
  stored as the reserved id `1`, which is how Telegram identifies General.

## `/about_karma` (any member)
Prints the rules message. In forums it works only in enabled topics, like the other commands.
In regular groups and private chats it works everywhere; in private chats the text is in Russian
(same as `/start`).

## Rules message (ru, agreed text; en is a translation)
After `/karma_on`, the bot first sends the line "✅ Карма-бот включён в этом топике!" and then
the rules message. `/about_karma` sends only the rules message.
```
🎮 Правила игры

Здесь мы помогаем друг другу расти в LinkedIn. Каждый лайк,
комментарий и репост — это чей-то шанс быть замеченным,
получить оффер или найти своих людей. Вместе мы сильнее любого алгоритма! 💪

Как это работает:
1. Делитесь ссылкой на свой пост в LinkedIn, чтобы другие
   могли поддержать вас там.
2. Поддержали чужой пост в LinkedIn (лайк, а лучше комментарий,
   а может, даже репост)? Поставьте любую реакцию на сообщение
   с этим постом здесь — и получите +1 к карме.

Я не проверяю саму поддержку в LinkedIn, я просто считаю реакции здесь.
Свои посты не считаются, снятая реакция — минус очко.

🔔 Хотите узнавать о новых постах сразу? Напишите мне /start в личку.

Добро возвращается — особенно в LinkedIn. Поехали! 🚀
```
The text has no command list: in groups `/karma`, `/top`, `/top_all` and `/stats` are admin-only,
and `/help` works only in private chats. If `post_cost > 0`, the line
"Публикация поста стоит {cost} очков кармы." is added before the 🔔 line. The language is the
group's language.

`/help` gets the three new commands in its admin section and `/about_karma` in the user
commands (ru and en).

## Approaches considered
- **A (chosen): new table `group_topics` (`chat_id`, `topic_id`, PK on both) plus one shared
  aiogram middleware/filter on the group message routers.** The check lives in one place, and
  `create_all` creates the new table on startup, so no manual migration is needed. Cost: one
  small DB query per forum message.
- B: a list column in `group_settings` plus a check in every handler. Needs an Alembic migration
  for the existing table, and it is easy to forget the check in a new handler.

## Constraints
- No existing forum supergroups use the bot (confirmed by the user), so the "off by default"
  rule breaks nothing.
- Add an Alembic migration file for the new table anyway, following `migrations/versions/`.
- Tests: follow the existing pytest suite (`tests/`).

## Delivery
Work goes on the `feature/karma-topics` branch with a PR on GitHub. It is merged into `main`
after the work is finished and the tests pass.

## Left to the builder
How to attach the filter in aiogram (outer middleware vs. router filter), the exact text
of the `/karma_off` and `/karma_topics` replies, and how topics are shown in the list
(topic id; Telegram's Bot API does not return topic names).
