# Karma Topics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In forum supergroups the bot works only in topics an admin enabled with `/karma_on`; `/about_karma` prints the rules.

**Architecture:** New table `group_topics` + `TopicRepository`. A router-level aiogram filter `KarmaTopicFilter` is attached to the `admin`, `commands` and `messages` routers; it passes non-forum chats and enabled topics. A new unfiltered `topics` router (registered first) holds `/karma_on`, `/karma_off`, `/karma_topics`.

**Tech Stack:** Python 3.11, aiogram 3, SQLAlchemy 2 async, Alembic, pytest + pytest-asyncio (`asyncio_mode = auto`).

**Spec:** `docs/superpowers/specs/2026-11-16-karma-topics-design.md`

## Global Constraints

- Forum = `message.chat.is_forum is True`. Non-forum groups and private chats behave exactly as today.
- Topic id of a message: `message.message_thread_id` if `message.is_topic_message` else `1` (General).
- Rules text (ru) is copied verbatim from the spec (no command list); extra line `Публикация поста стоит {cost} очков кармы.` only when `post_cost > 0`, placed right before the `🔔` line.
- `/karma_on` sends `✅ Карма-бот включён в этом топике!` first, then the rules as a second message.
- Group language from `GroupSettings.language`; private chats use `ru`.
- Run tests with the project venv: `python -m pytest -q`.

## Review Focus

- `/karma_on` in the General topic (no `message_thread_id`) must enable topic `1`, and plain messages in General must then pass the filter.
- A reply inside a non-forum supergroup carries `message_thread_id`; the filter must ignore it (only `is_forum` chats are filtered).
- `/karma_on` sent twice must not crash on the duplicate primary key.
- `/karma_on` by a non-admin must not enable anything.
- Messages without `chat` (or channel posts) must not crash the filter.

---

### Task 1: `GroupTopic` model, repository, migration

**Files:**
- Create: `bot/models/group_topic.py`, `migrations/versions/004_add_group_topics.py`
- Modify: `bot/models/__init__.py`, `bot/database/repositories.py`, `bot/database/__init__.py`
- Test: `tests/test_repositories.py` (new class `TestTopicRepository`)

**Interfaces:**
- Produces: model `GroupTopic(chat_id: BigInteger PK, topic_id: BigInteger PK, created_at)`, table `group_topics`.
- Produces: `TopicRepository(session)` with
  `async enable(chat_id: int, topic_id: int) -> bool` (True if newly enabled),
  `async disable(chat_id: int, topic_id: int) -> bool` (True if it was enabled),
  `async is_enabled(chat_id: int, topic_id: int) -> bool`,
  `async list_topics(chat_id: int) -> list[int]` (sorted).

- [ ] **Step 1: Write failing tests** `test_enable_new_returns_true`, `test_enable_twice_returns_false` (second call False, `list_topics == [5]`), `test_disable` (True then False), `test_is_enabled_scoped_by_chat` (enabled in chat -1 topic 5 → not enabled in chat -2 topic 5), `test_list_topics_sorted` (enable 9, 1, 5 → `[1, 5, 9]`).
- [ ] **Step 2: Run** `python -m pytest tests/test_repositories.py -k TopicRepository -q` → FAIL (import error).
- [ ] **Step 3: Implement** the model (follow `bot/models/settings.py`), export it, `TopicRepository` (check existence before insert, commit on enable/disable), export from `bot/database`. Migration `004`: `revision='004'`, `down_revision='003'`, `create_table('group_topics', chat_id BigInteger, topic_id BigInteger, created_at DateTime(timezone=True) server_default now(), PK(chat_id, topic_id))`.
- [ ] **Step 4: Run** the same command → PASS; full suite green.
- [ ] **Step 5: Commit** `feat: add group_topics table and TopicRepository`.

### Task 2: Topic helpers and `KarmaTopicFilter`

**Files:**
- Create: `bot/handlers/topics.py` (helpers + filter now, handlers in Task 4)
- Test: `tests/test_topics.py`

**Interfaces:**
- Consumes: `TopicRepository.is_enabled`.
- Produces: `GENERAL_TOPIC_ID = 1`; `is_forum(message) -> bool`; `topic_id_of(message) -> int`;
  `class KarmaTopicFilter(aiogram.filters.Filter)` with `async __call__(message) -> bool`; uses module-level `get_session` (patchable in tests).

- [ ] **Step 1: Write failing tests** (messages as `SimpleNamespace`, session patched like `patch_commands_session`):
  `test_topic_id_of_topic_message` (`is_topic_message=True, message_thread_id=7` → 7),
  `test_topic_id_of_general` (`is_topic_message=None, message_thread_id=None` → 1),
  `test_filter_passes_private_chat`, `test_filter_passes_non_forum_supergroup_reply` (`is_forum=None, message_thread_id=42` → True, no DB call),
  `test_filter_blocks_disabled_topic`, `test_filter_passes_enabled_topic`, `test_filter_passes_enabled_general`,
  `test_filter_passes_message_without_chat` (`chat=None` → True; handlers already guard).
- [ ] **Step 2: Run** `python -m pytest tests/test_topics.py -q` → FAIL.
- [ ] **Step 3: Implement** helpers and filter in `bot/handlers/topics.py`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: add karma topic filter`.

### Task 3: Rules text and i18n

**Files:**
- Modify: `bot/i18n/ru.py`, `bot/i18n/en.py`
- Create: `bot/services/rules.py`
- Test: `tests/test_rules.py`

**Interfaces:**
- Produces i18n keys (ru and en): `rules_text` (with a `{post_cost_line}` placeholder on its own line before `🔔`), `rules_post_cost` (`Публикация поста стоит {cost} очков кармы.`), `karma_topic_enabled`, `karma_topic_disabled`, `karma_topic_not_enabled`, `karma_topics_list` (`{topics}`), `karma_topics_empty`, `forum_only_command`. Add `/about_karma` to `help_text` and `commands_list` user commands, and `/karma_on`, `/karma_off`, `/karma_topics` to the admin section of `help_text`.
- Produces: `build_rules_text(lang: str, post_cost: int) -> str` in `bot/services/rules.py` (no blank-line gap left when `post_cost == 0`).

- [ ] **Step 1: Write failing tests** `test_rules_starts_with_title` (ru text `.strip()` starts with `🎮 Правила игры`), `test_rules_has_no_command_list` (no `/karma`, `/top`, `/help` in ru and en), `test_rules_no_cost_line_when_free` (no `Публикация поста стоит`, no `\n\n\n`), `test_rules_cost_line_when_paid` (cost 3 → contains `Публикация поста стоит 3 очков кармы.`), `test_rules_en_available` (en text starts with `🎮 Game rules`), `test_help_lists_new_commands` (ru/en `help_text` contain `/about_karma`, `/karma_on`, `/karma_off`, `/karma_topics`).
- [ ] **Step 2: Run** `python -m pytest tests/test_rules.py -q` → FAIL.
- [ ] **Step 3: Implement** the strings (ru verbatim from the spec; en a faithful translation) and `build_rules_text`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: add game rules text`.

### Task 4: `/karma_on`, `/karma_off`, `/karma_topics`, `/about_karma` and router wiring

**Files:**
- Modify: `bot/handlers/topics.py` (router + handlers), `bot/handlers/commands.py` (`/about_karma`), `bot/handlers/__init__.py`
- Test: `tests/test_topics.py`

**Interfaces:**
- Consumes: `TopicRepository`, `is_forum`, `topic_id_of`, `KarmaTopicFilter`, `build_rules_text`, `is_admin` (from `bot.handlers.admin`), `SettingsRepository.get_or_create`.
- Produces: `bot.handlers.topics.router` (name `"topics"`), handlers `cmd_karma_on`, `cmd_karma_off`, `cmd_karma_topics`; `commands.cmd_about_karma`.
- Wiring in `get_routers()`: `[topics_router, admin_router, commands_router, reactions_router, messages_router]`; `router.message.filter(KarmaTopicFilter())` on admin, commands and messages routers (in `__init__.py`, so handler modules stay unaware).

- [ ] **Step 1: Write failing tests:**
  `test_karma_on_non_forum_replies_forum_only` (nothing stored),
  `test_karma_on_non_admin_rejected` (`admin_only` reply, `list_topics == []`),
  `test_karma_on_enables_and_sends_rules` (two replies: first `karma_topic_enabled`, second `build_rules_text("ru", 0)`; topic 7 stored),
  `test_karma_on_general_enables_topic_1`,
  `test_karma_on_twice_ok` (no exception, rules sent again),
  `test_karma_off_disables` and `test_karma_off_not_enabled` (`karma_topic_not_enabled`),
  `test_karma_topics_lists_links` (chat `-1001234567890`, topics 1 and 7 → reply contains `https://t.me/c/1234567890/7`; General shown as its own label),
  `test_about_karma_in_group_uses_group_settings` (`language="en"` → en rules),
  `test_about_karma_private_ru`,
  `test_routers_order_and_filters` (`get_routers()[0].name == "topics"`; admin/commands/messages routers have a `KarmaTopicFilter` in `router.message._handler.filters`, topics router does not).
- [ ] **Step 2: Run** `python -m pytest tests/test_topics.py -q` → FAIL.
- [ ] **Step 3: Implement** handlers (replies via `message.reply`, so they land in the same topic) and wiring.
- [ ] **Step 4: Run** full suite `python -m pytest -q` → all PASS.
- [ ] **Step 5: Commit** `feat: enable karma per forum topic, add /about_karma`.

### Task 5: Docs and PR

**Files:**
- Modify: `README.md` (Admin Commands + Usage: forum topics note, `/about_karma`)

- [ ] **Step 1:** Update README.
- [ ] **Step 2:** Full suite green.
- [ ] **Step 3:** Commit `docs: describe karma topics`, push, open PR `feature/karma-topics → main`.
