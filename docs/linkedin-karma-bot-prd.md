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
3. Maintains each participant's karma (weekly and total)
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

**Long-term karma**:
- Total number of likes over all time
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
```

**Newcomer:**
```
📝 @username 🌱 asks for support
Per week — Support: 0 | Posts: 1
```

**Regular participant:**
```
📝 @username asks for support
Per week — Support: ⭐⭐⭐ (8) | Posts: 2
```

**Veteran:**
```
📝 @username 🎖️ (47) asks for support
Per week — Support: ⭐⭐ (4) | Posts: 1
```

**Inactive:**
```
📝 @username asks for support
Per week — Support: 0 | Posts: 3
```

### 6. Bot Commands

#### For all users

| Command        | Description                    |
|----------------|--------------------------------|
| `/karma`       | Show your karma (weekly + total) |
| `/karma @user` | Show user's karma              |
| `/top`         | Top-10 by weekly karma         |
| `/top_all`     | Top-10 by long-term karma      |
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
| Multiple emojis on one post  | Counted as 1 like           |
| Multiple links in one message| Counted as 1 post           |
| User left group              | Karma is preserved          |
| Message edit (adding link)   | Not tracked                 |

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
