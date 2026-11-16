# Short LinkedIn links (lnkd.in/p/...)

## Why
The LinkedIn mobile app shares posts as short links like `https://lnkd.in/p/eMunJYSY`.
The bot ignores them today, so such posts are not registered and get no karma.

## Behaviour
- Accept `lnkd.in/p/<code>` as a LinkedIn post link: `http` or `https`, with or without `www.`,
  query string allowed. Works in plain text and in Telegram `url` / `text_link` entities.
- Do **not** accept `lnkd.in/<code>` without `/p/`: LinkedIn uses those to wrap external sites.
- Store the link as is. The bot does not follow redirects (no network calls).
- `/help` (ru and en) lists `lnkd.in/p/...` among supported links.

## Approaches
- **Chosen:** extend `LINKEDIN_PATTERN` in `bot/services/linkedin.py` with an `lnkd.in/p/` branch.
- Rejected: accept any `lnkd.in` link (registers external sites as posts); resolve the short
  link to the full URL (network call per message, failure modes, no benefit since URLs are not deduplicated).

## Delivery
Branch `feature/lnkd-short-links`, PR, merge into `main`, deploy (approved by the owner).
