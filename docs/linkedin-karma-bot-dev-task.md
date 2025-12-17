# Development Task: LinkedIn Karma Bot

## Project Overview

Create a Telegram bot for LinkedIn content mutual support groups. The bot tracks reactions to messages with LinkedIn links and maintains a participant karma system.

**PRD**: see `linkedin-karma-bot-prd.md`

---

## Technology Stack

| Component      | Technology                    |
|----------------|-------------------------------|
| Language       | Python 3.11+                  |
| Telegram API   | python-telegram-bot (v20+) or aiogram (v3+) |
| Database       | PostgreSQL                    |
| ORM            | SQLAlchemy 2.0 or asyncpg    |
| Migrations     | Alembic                       |
| Containerization | Docker + Docker Compose    |
| Configuration  | Environment variables (.env)  |

---

## Project Structure

```
linkedin-karma-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration from env
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── messages.py      # LinkedIn message handling
│   │   ├── reactions.py     # Reaction handling
│   │   ├── commands.py      # User commands
│   │   └── admin.py         # Admin commands
│   ├── services/
│   │   ├── __init__.py
│   │   ├── karma.py         # Karma logic
│   │   ├── linkedin.py      # LinkedIn link parsing
│   │   └── stats.py         # Statistics
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── reaction.py
│   │   └── settings.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   └── repositories.py
│   └── i18n/
│       ├── __init__.py
│       ├── ru.py
│       └── en.py
├── migrations/
│   └── versions/
├── tests/
│   ├── __init__.py
│   ├── test_karma.py
│   ├── test_linkedin.py
│   └── test_handlers.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
├── .env.example
└── README.md
```

---

## Development Stages

### Stage 1: Infrastructure

**Tasks:**
1. Initialize project with Poetry or pip
2. Set up Docker and Docker Compose (bot + PostgreSQL)
3. Create configuration via environment variables
4. Set up database connection
5. Create SQLAlchemy models and Alembic migrations

**Environment variables (.env.example):**
```env
# Telegram
TELEGRAM_BOT_TOKEN=your_token_here

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/karma_bot

# Defaults
DEFAULT_LANGUAGE=ru
DEFAULT_KARMA_PERIOD=7
DEFAULT_VETERAN_THRESHOLD=30
DEFAULT_POST_COST=0
```

**Result:** Project runs in Docker, connects to database.

---

### Stage 2: Data Models

**Tables:**

```sql
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    display_name VARCHAR(255),
    first_seen_at TIMESTAMP DEFAULT NOW(),
    first_post_at TIMESTAMP NULL,
    karma_total INTEGER DEFAULT 0
);

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    message_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    author_id BIGINT REFERENCES users(telegram_id),
    linkedin_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(chat_id, message_id)
);

CREATE TABLE reactions (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(telegram_id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(post_id, user_id)
);

CREATE TABLE settings (
    chat_id BIGINT PRIMARY KEY,
    language VARCHAR(2) DEFAULT 'ru',
    karma_period_days INTEGER DEFAULT 7,
    veteran_threshold INTEGER DEFAULT 30,
    post_cost INTEGER DEFAULT 0
);
```

**Result:** Migrations created and applied.

---

### Stage 3: Basic Bot Logic

**Tasks:**
1. Set up Telegram handlers
2. Parse LinkedIn links (regex):
   ```python
   LINKEDIN_PATTERN = r'https?://(?:www\.)?linkedin\.com/(?:posts|feed/update|pulse)/[^\s]+'
   ```
3. On link detection:
   - Create/update user
   - Save post
   - Send message with author's karma

**Result:** Bot responds to LinkedIn links.

---

### Stage 4: Reaction Handling

**Tasks:**
1. Subscribe to `message_reaction` event
2. On reaction add:
   - Check that message is a LinkedIn post
   - Check that it's not a self-like
   - Add reaction (INSERT ... ON CONFLICT DO NOTHING)
   - Increase reactor's karma_total
3. On reaction remove:
   - Delete from reactions table
   - Decrease karma_total

**Important:** Multiple emojis on one post = 1 reaction.

**Result:** Karma calculated correctly.

---

### Stage 5: Karma Service

**Methods:**
```python
class KarmaService:
    async def get_weekly_karma(self, user_id: int, period_days: int) -> int:
        """Number of unique posts supported in period"""

    async def get_total_karma(self, user_id: int) -> int:
        """Total karma over all time"""

    async def get_weekly_posts_count(self, user_id: int, period_days: int) -> int:
        """Number of user's posts in period"""

    async def is_newcomer(self, user_id: int) -> bool:
        """Check: has user published posts"""

    async def is_veteran(self, user_id: int, threshold: int) -> bool:
        """Check: karma_total >= threshold"""

    def karma_to_stars(self, karma: int) -> str:
        """Convert karma to stars"""
        # 0 -> ""
        # 1-2 -> "⭐"
        # 3-5 -> "⭐⭐"
        # 6-10 -> "⭐⭐⭐"
        # 11-20 -> "⭐⭐⭐⭐"
        # 21+ -> "⭐⭐⭐⭐⭐"
```

**Result:** Karma logic encapsulated.

---

### Stage 6: Message Formatting

**Response format for LinkedIn post:**

```python
def format_post_message(user, weekly_karma, weekly_posts, is_newcomer, is_veteran, total_karma, lang):
    # Line 1: status
    if is_newcomer:
        line1 = f"📝 @{user.username} 🌱 {t('asks_support', lang)}"
    elif is_veteran:
        line1 = f"📝 @{user.username} 🎖️ ({total_karma}) {t('asks_support', lang)}"
    else:
        line1 = f"📝 @{user.username} {t('asks_support', lang)}"

    # Line 2: weekly statistics
    stars = karma_to_stars(weekly_karma)
    karma_display = f"{stars} ({weekly_karma})" if stars else str(weekly_karma)
    line2 = f"{t('per_week', lang)} — {t('support', lang)}: {karma_display} | {t('posts', lang)}: {weekly_posts}"

    return f"{line1}\n{line2}"
```

**Result:** Messages formatted per specification.

---

### Stage 7: User Commands

| Command        | Implementation                    |
|----------------|-----------------------------------|
| `/karma`       | Show own weekly + total karma     |
| `/karma @user` | Show specified user's karma       |
| `/top`         | Top-10 by weekly karma            |
| `/top_all`     | Top-10 by total karma             |
| `/stats`       | Total participants, posts, reactions per week |
| `/help`        | Command help                      |

**Result:** All user commands work.

---

### Stage 8: Admin Commands

| Command          | Implementation                    |
|------------------|-----------------------------------|
| `/set_lang ru\|en` | Save language in settings         |
| `/set_period N`  | Save karma period                 |
| `/set_veteran N` | Save veteran threshold            |
| `/set_post_cost N` | Save post cost                    |
| `/reset_karma @user` | Zero karma_total and delete reactions |
| `/export`       | CSV with columns: username, karma_weekly, karma_total, posts_weekly |

**Permission check:** use `get_chat_member()` to check administrator.

**Result:** Admins can configure bot.

---

### Stage 9: Localization

**i18n files:**

```python
# i18n/ru.py
RU = {
    "asks_support": "просит поддержки",
    "per_week": "За неделю",
    "support": "Поддержка",
    "posts": "Постов",
    "newcomer": "новичок",
    "veteran": "ветеран",
    "your_karma": "Ваша карма",
    "weekly": "за неделю",
    "total": "всего",
    # ...
}

# i18n/en.py
EN = {
    "asks_support": "asks for support",
    "per_week": "This week",
    "support": "Support",
    "posts": "Posts",
    "newcomer": "newcomer",
    "veteran": "veteran",
    "your_karma": "Your karma",
    "weekly": "this week",
    "total": "total",
    # ...
}
```

**Result:** Bot works in two languages.

---

### Stage 10: Testing and Deployment

**Tests:**
- Unit tests for KarmaService
- LinkedIn link parsing tests
- Integration tests for handlers (pytest + pytest-asyncio)

**Docker Compose:**
```yaml
version: '3.8'
services:
  bot:
    build: .
    env_file: .env
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: karma_bot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: karma_bot
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  pgdata:
```

**Result:** Bot deploys with one command `docker-compose up -d`.

---

## Readiness Criteria

- [ ] Bot starts in Docker
- [ ] Recognizes LinkedIn links in messages
- [ ] Tracks reaction additions and removals
- [ ] Correctly calculates weekly and total karma
- [ ] Displays statuses: newcomer 🌱, veteran 🎖️
- [ ] All user commands work
- [ ] Admin commands work (with permission checks)
- [ ] Localization RU/EN
- [ ] Basic tests exist
- [ ] README with deployment instructions

---

## Starting Development

```bash
# Clone and navigate to directory
cd linkedin-karma-bot

# Create .env from example
cp .env.example .env
# Fill in TELEGRAM_BOT_TOKEN

# Start
docker-compose up -d

# View logs
docker-compose logs -f bot
```
