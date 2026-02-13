# PRD: LinkedIn Karma Bot

## Overview

**Name**: LinkedIn Karma Bot  
**Purpose**: Telegram bot for LinkedIn content mutual support groups. Tracks participant activity and maintains a karma system.

---

## Problem

In LinkedIn post mutual support groups, there are "consumers" - people who only ask for likes on their posts but don't support others themselves. There's no transparent mechanism to track each participant's contribution.

---

## Solution

A bot that:
1. Recognizes LinkedIn post links in group messages
2. Records reactions (emojis) to these messages as support
3. Maintains each participant's karma (weekly and all-time)
4. Shows author statistics when a new link is posted

---

## Functional Requirements

### 1. LinkedIn Link Tracking

- Bot monitors all messages in the group
- Recognizes links:
  - `linkedin.com/posts/...`
  - `linkedin.com/feed/update/...`
  - `linkedin.com/pulse/...`
- Saves: message ID, author, link, publication time

### 2. Reaction Tracking

- Tracks reaction additions and **removals** (emojis)
- When a reaction is removed - karma decreases
- **One post = maximum 1 point** (regardless of emoji count)
- Self-likes are not counted
- Replies to messages **are not counted**

**Requirement**: Bot must be a group administrator to track reactions.

### 3. Karma System

**Weekly karma (primary)**:
- Number of unique posts the user has supported in the last 7 days
- Sliding window
- Displayed as stars:

| Likes per week | Display |
|----------------|---------|
| 0              | (empty) |
| 1-2            | ⭐      |
| 3-5            | ⭐⭐    |
| 6-10           | ⭐⭐⭐  |
| 11-20          | ⭐⭐⭐⭐|
| 21+            | ⭐⭐⭐⭐⭐|

**All-time support (required, always visible)**:
- Number of unique posts the user has supported in this group over all time
- Stored as per-group metric
- Always shown in bot messages, including value `0`

**Long-term karma**:
- Equals the all-time support value in the group
- Used for "veteran" status

### 4. User Statuses

| Status   | Condition                                    | Emoji |
|----------|----------------------------------------------|-------|
| Newcomer | Never published a LinkedIn post              | 🌱    |
| Veteran  | Long-term karma ≥ threshold (default: 30)   | 🎖️    |

### 5. Message on Post Publication

When a user posts a LinkedIn link, the bot responds:

**Message format:**
```
📝 @username [status] asks for support
Per week — Support: [stars] ([number]) | Posts: [number]
[all_time_count] — supported all-time
```

**Newcomer:**
```
📝 @username 🌱 asks for support
Per week — Support: 0 | Posts: 1
0 — supported all-time
```

**Regular participant:**
```
📝 @username asks for support
Per week — Support: ⭐⭐⭐ (8) | Posts: 2
47 — supported all-time
```

**Veteran:**
```
📝 @username 🎖️ (47) asks for support
Per week — Support: ⭐⭐ (4) | Posts: 1
47 — supported all-time
```

**Inactive:**
```
📝 @username asks for support
Per week — Support: 0 | Posts: 3
47 — supported all-time
```

### 6. Bot Commands

#### For all users

| Command        | Description                    |
|----------------|--------------------------------|
| `/karma`       | Show your karma (weekly + all-time support) |
| `/karma @user` | Show user's karma              |
| `/top`         | Top-10 by weekly karma         |
| `/top_all`     | Top-10 by all-time support     |
| `/stats`       | Group statistics               |
| `/help`        | Help                           |

#### For administrators

| Command                | Description                              | Default |
|------------------------|------------------------------------------|---------|
| `/set_lang ru` / `/set_lang en` | Bot language for group            | ru      |
| `/set_period N`        | Weekly karma period (days)               | 7       |
| `/set_veteran N`       | Veteran status threshold                 | 30      |
| `/set_post_cost N`     | How many likes a post "costs"            | 0       |
| `/reset_karma @user`   | Reset user's karma                       | —       |
| `/export`              | Export statistics to CSV                 | —       |

### 7. Localization

Bot supports two languages:
- Russian (default)
- English

Language is a group setting, selected by administrator with `/set_lang` command.

Required localization keys for post message formatting:
- `asks_support` (e.g., RU: `просит поддержки`, EN: `asks for support`)
- `supported_all_time` (e.g., RU: `{count} — поддержал за всё время`, EN: `{count} — supported all-time`)

---

## Non-Functional Requirements

### Database
- **PostgreSQL**

### Performance
- Message processing < 1 sec
- Support for groups up to 1000 participants

### Deployment
- Docker container
- Environment variables for configuration

### Limitations
- One bot instance = one group
- For multiple groups - separate instances

---

## Data Structure

```sql
-- Users
users:
  - telegram_id (PK)
  - username
  - display_name
  - first_seen_at
  - first_post_at (NULL = newcomer)
  - karma_total (cache)

-- Posts with LinkedIn links
posts:
  - id (PK)
  - message_id
  - chat_id
  - author_id (FK → users)
  - linkedin_url
  - created_at

-- Reactions
reactions:
  - id (PK)
  - post_id (FK → posts)
  - user_id (FK → users)
  - created_at
  - UNIQUE(post_id, user_id)

-- Per-group user karma / all-time support
user_karma:
  - id (PK)
  - user_id (FK → users.telegram_id)
  - chat_id
  - karma_total (all-time support in group)
  - UNIQUE(user_id, chat_id)

-- Group settings
settings:
  - chat_id (PK)
  - language ('ru' | 'en', default: 'ru')
  - karma_period_days (default: 7)
  - veteran_threshold (default: 30)
  - post_cost (default: 0)
```

---

## Edge Cases

| Situation                    | Behavior                    |
|------------------------------|-----------------------------|
| Self-like                    | Not counted                 |
| Reaction removal             | Karma decreases             |
| Emoji change (reaction stays)| Karma is unchanged          |
| Remove one of many emojis    | Karma is unchanged          |
| Remove all reactions         | Karma decreases by 1        |
| Multiple emojis on one post  | Counted as 1 like           |
| Multiple links in one message| Counted as 1 post           |
| User left group              | Karma is preserved          |
| Message edit (adding link)   | Not tracked                 |

---

## Acceptance Criteria

1. Post publication messages (`newcomer`, `regular`, `veteran`, `inactive`) always include an all-time support line:
   - `{count} — supported all-time` (EN)
   - `{count} — поддержал за всё время` (RU)
2. For users with no historical support, all-time line shows `0`.
3. Switching one emoji to another on the same post does not change all-time support.
4. Removing one of multiple emojis on the same post does not change all-time support.
5. Removing all reactions from a supported post decreases all-time support by 1.
6. `/karma` includes weekly and all-time support values.

---

## MVP (v1.0)

- [x] LinkedIn link tracking
- [x] Reaction tracking (add and remove)
- [x] Weekly and long-term karma
- [x] Statuses: newcomer, veteran
- [x] Message on post publication
- [x] Commands: `/karma`, `/top`, `/top_all`, `/help`
- [x] Admin commands: `/set_period`, `/set_veteran`
- [x] Localization: RU + EN

---

## Future Improvements (v2.0+)

- LinkedIn API integration (verify real likes)
- Gamification (badges, levels, achievements)
- Reminders for inactive participants
- Weekly activity digest
- Support for multiple groups with one bot
