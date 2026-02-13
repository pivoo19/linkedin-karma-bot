# Dev Task: Always Show All-Time Supported Publications

## Date
2026-02-13

## Source
- Product requirement: `docs/linkedin-karma-bot-prd.md`
- Relevant sections:
  - `Karma System` (all-time support must be always visible)
  - `Message on Post Publication` (new required line)
  - `Localization` (`supported_all_time` key)
  - `Acceptance Criteria`

## Goal
Implement UI/response changes so the bot always shows how many publications a user supported all-time in the current group.

Required display format (RU):
- `{count} — поддержал за всё время`

## Scope
### In scope
1. Add all-time support line to post publication messages (`newcomer`, `regular`, `veteran`).
2. Ensure `/karma` output includes all-time support explicitly (group and private output).
3. Add localization key(s) for all-time support line (`ru`, `en`).
4. Keep reaction math unchanged (already fixed for emoji-switch edge cases).
5. Add/update tests for new output.

### Out of scope
1. Changing karma algorithms or storage model.
2. Refactoring unrelated modules.
3. Deployment/infrastructure changes.

## Important Constraints
1. Group command access policy must remain unchanged:
- `/karma`, `/top`, `/top_all`, `/stats` are admin-only in groups.
- In private chat these commands work without admin check.

2. Data source for all-time support:
- Use `user_karma.karma_total` for the corresponding `chat_id`.

## Implementation Plan
1. Localization
- Update `bot/i18n/ru.py`:
  - add key `supported_all_time`: `{count} — поддержал за всё время`
- Update `bot/i18n/en.py`:
  - add key `supported_all_time`: `{count} — supported all-time`

2. Post message formatting
- Update `bot/handlers/messages.py`:
  - fetch all-time support (already available via `UserKarmaRepository.get_total_karma(...)`)
  - append a dedicated line to every post response using `t("supported_all_time", ...)`
  - apply for newcomer/regular/veteran templates consistently

3. `/karma` output
- Update `bot/handlers/commands.py`:
  - Group mode: keep weekly + total, add explicit all-time support line.
  - Private mode (per chat block): include explicit all-time support line.

4. Optional cleanup (if needed for readability)
- If message templates become too long, consider helper function in handler scope only.

## Files Expected to Change
- `bot/handlers/messages.py`
- `bot/handlers/commands.py`
- `bot/i18n/ru.py`
- `bot/i18n/en.py`
- tests:
  - update existing tests if assertions rely on old strings
  - add/extend handler tests

## Test Plan
1. Unit/handler tests
- Post message includes all-time line for:
  - newcomer
  - regular
  - veteran
- `/karma` in group includes all-time support line.
- `/karma` in private includes all-time support line for each chat section.
- Formatting for `count = 0` is correct.

2. Regression tests
- Existing reaction transition tests remain green:
  - emoji switch does not change karma
  - partial emoji removal does not change karma
  - full removal decrements karma

3. Full suite
- Run: `pytest -q`

## Definition of Done
1. All post publication responses contain:
- weekly line
- posts line
- all-time support line (`{count} — поддержал за всё время` / EN equivalent)

2. `/karma` clearly displays all-time support in both contexts:
- group
- private

3. Admin-only behavior in groups remains unchanged.

4. `pytest -q` passes.

5. README/help text updated if output examples changed.
