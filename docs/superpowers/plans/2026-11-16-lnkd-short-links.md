# Short LinkedIn Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recognise `lnkd.in/p/<code>` short links as LinkedIn posts.

**Architecture:** One extra alternative in `LINKEDIN_PATTERN` (`bot/services/linkedin.py`); every caller (`is_linkedin_url`, `extract_linkedin_urls`, `extract_linkedin_urls_from_message`, `is_linkedin_post`) picks it up.

**Tech Stack:** Python 3.11, `re`, pytest.

**Spec:** `docs/superpowers/specs/2026-11-16-lnkd-short-links-design.md`

## Global Constraints

- Accept only `lnkd.in/p/<code>` (http/https, optional `www.`, query allowed); reject `lnkd.in/<code>`.
- No network calls; the link is stored as written.

## Review Focus

- `lnkd.in/p/` with nothing after it must not match.
- A short link followed by punctuation or text in the same message: the match stops at whitespace, like the existing patterns.
- Uppercase `LNKD.IN` matches (pattern is case-insensitive).

---

### Task 1: Accept lnkd.in/p links

**Files:**
- Modify: `bot/services/linkedin.py:12-21`, `bot/i18n/ru.py:70-73`, `bot/i18n/en.py:70-73`, `README.md` (supported links, if listed)
- Test: `tests/test_linkedin.py`

- [ ] **Step 1: Write failing tests** in a new class `TestShortLinks`:
  `test_short_link_extracted` (`"Мой пост https://lnkd.in/p/eMunJYSY"` → `["https://lnkd.in/p/eMunJYSY"]`),
  `test_short_link_is_linkedin_url` (http, `www.`, `?trk=x` variants → True),
  `test_short_link_without_p_rejected` (`https://lnkd.in/dAbC123` → `is_linkedin_url` False, `extract_linkedin_urls` `[]`),
  `test_short_link_empty_code_rejected` (`https://lnkd.in/p/` → False),
  `test_short_link_from_text_link_entity` (message with `text_link` entity url `https://lnkd.in/p/eMunJYSY` → extracted),
  `test_help_lists_short_links` (ru/en `help_text` contain `lnkd.in/p/...`).
- [ ] **Step 2: Run** `python -m pytest tests/test_linkedin.py -q` → new tests FAIL.
- [ ] **Step 3: Implement:** add `|https?://(?:www\.)?lnkd\.in/p/[^\s]+` to the pattern (keep case-insensitive), update the comment, add `- lnkd.in/p/...` to supported links in ru/en help.
- [ ] **Step 4: Run** full suite → all PASS.
- [ ] **Step 5: Commit** `feat: accept lnkd.in/p short links`.
