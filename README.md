# LinkedIn Karma Bot

A Telegram bot that encourages sharing quality LinkedIn content in group chats through a karma-based reward system. Users earn karma points when their shared LinkedIn posts receive reactions from other members.

## Features

- **LinkedIn URL Detection**: Automatically detects and validates LinkedIn post, feed, and Pulse article URLs
- **Karma System**: Users earn karma points when others react to their shared posts
- **User Status Tracking**:
  - **Newcomers**: Users who haven't made their first post yet
  - **Veterans**: Users who have accumulated significant karma (configurable threshold)
  - **Reaction Management**: Track and manage reactions to posts with automatic karma updates
  - **Group Settings**: Customizable settings per Telegram group:
  - Language preferences (Russian/English)
  - Karma calculation period (default: 7 days)
  - Veteran threshold (default: 30 karma points)
  - Post cost in karma (optional barrier to posting)
- **Statistics**: View top users, karma leaderboards, and group statistics
- **Database Support**: Works with both SQLite (development) and PostgreSQL (production)

## Tech Stack

- **Python 3.11+**
- **aiogram 3.13**: Modern async Telegram bot framework
- **SQLAlchemy 2.0**: Async ORM for database operations
- **Alembic**: Database migrations
- **Pydantic**: Settings and configuration management
- **pytest**: Testing framework with async support

## Project Structure

```
linkedin-karma-bot/
├── bot/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py      # Database connection setup
│   │   └── repositories.py    # Data access layer
│   ├── handlers/              # Telegram message handlers
│   │   └── __init__.py
│   ├── i18n/                  # Internationalization
│   │   └── __init__.py
│   ├── models/                # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── reaction.py
│   │   └── settings.py
│   └── services/              # Business logic
│       ├── __init__.py
│       ├── linkedin.py        # LinkedIn URL parsing
│       ├── karma.py           # Karma calculations
│       └── stats.py           # Statistics
├── migrations/                # Alembic database migrations
├── scripts/
│   └── simulator.py           # CLI simulator for testing
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures
│   ├── test_linkedin.py       # LinkedIn parser tests
│   ├── test_karma.py          # Karma service tests
│   └── test_repositories.py  # Repository tests
├── .env.example               # Example environment variables
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Docker services configuration
├── pytest.ini                 # Pytest configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Setup

### Local Development (SQLite)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd linkedin-karma-bot
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Telegram bot token
   ```

5. **Run the bot**:
   ```bash
   python -m bot.main
   ```

   Database tables are created automatically on first startup.

### Docker Deployment (PostgreSQL)

1. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f bot
   ```

4. **Stop the services**:
   ```bash
   docker-compose down
   ```

## Configuration

Configuration is managed through environment variables. See `.env.example` for all available options:

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token (from @BotFather) | Required |
| `DATABASE_URL` | Database connection URL | `sqlite+aiosqlite:///./karma_bot.db` |
| `DEFAULT_LANGUAGE` | Default language (ru/en) | `ru` |
| `DEFAULT_KARMA_PERIOD` | Default karma period in days | `7` |
| `DEFAULT_VETERAN_THRESHOLD` | Karma points needed for veteran status | `30` |
| `DEFAULT_POST_COST` | Karma cost to post (0 = free) | `0` |

### Database URLs

- **SQLite** (development): `sqlite+aiosqlite:///./karma_bot.db`
- **PostgreSQL** (production): `postgresql+asyncpg://user:password@localhost:5432/karma_bot`

## Bot Commands

### User Commands

- `/start` - Start the bot and see welcome message
- `/help` - Show help and available commands
- `/karma` - View your current karma and statistics
- `/top` - View top users by karma in this group
- `/top_all` - View top users by total karma in this group
- `/stats` - View group statistics

### Admin Commands

- `/set_lang <ru|en>` - Set group language
- `/set_period <days>` - Set karma calculation period
- `/set_veteran <points>` - Set veteran threshold
- `/set_post_cost <points>` - Set karma cost to post
- `/reset_karma @username` - Reset user's karma to zero
- `/export` - Export group statistics as CSV file

## Usage

1. **Add the bot to a Telegram group**
2. **Grant admin permissions** (required for admin commands)
3. **Share LinkedIn posts** in the group:
   - Post any LinkedIn URL (posts, articles, feed updates)
   - Other members can react to your post
   - Earn +1 karma for each reaction
4. **View your karma**: Use `/karma` to see your current karma and status
5. **Compete on the leaderboard**: Use `/top` or `/top_all` to see who has the most karma

## Development

### Running Tests

Run the full test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=bot --cov-report=html --cov-report=term-missing
```

Run specific test file:
```bash
pytest tests/test_linkedin.py
```

Run specific test:
```bash
pytest tests/test_karma.py::TestKarmaService::test_karma_to_stars_zero
```

### CLI Simulator

Test bot functionality without Telegram using the CLI simulator:

**Create a post**:
```bash
python scripts/simulator.py post 123456 johndoe "https://linkedin.com/posts/johndoe_test"
```

**React to a post**:
```bash
python scripts/simulator.py react 789012 janedoe 1
```

**Remove a reaction**:
```bash
python scripts/simulator.py unreact 789012 1
```

**View user karma**:
```bash
python scripts/simulator.py karma 123456
```

**View top users**:
```bash
python scripts/simulator.py top 10
```

**View statistics**:
```bash
python scripts/simulator.py stats
```

### Database Migrations

The current project initializes schema automatically on startup via SQLAlchemy:

- `bot/database/connection.py` -> `init_db()` -> `Base.metadata.create_all`

Migration scripts are stored in `migrations/versions/`.

## API Reference

### LinkedIn Parser

```python
from bot.services.linkedin import extract_linkedin_urls, is_linkedin_post

# Extract all LinkedIn URLs from text
urls = extract_linkedin_urls(text)

# Check if a URL is a valid LinkedIn post
is_valid = is_linkedin_post(url)
```

### Karma Service

```python
from bot.services.karma import KarmaService

service = KarmaService(session)

# Convert karma to stars
stars = KarmaService.karma_to_stars(karma_points)

# Check if user is a newcomer
is_new = await service.is_newcomer(user_id)

# Check if user is a veteran
is_vet = await service.is_veteran(user_id, threshold=30)

# Get user's total karma
karma = await service.get_total_karma(user_id)

# Get weekly post count
posts = await service.get_weekly_posts_count(user_id, chat_id, period_days=7)
```

### Repositories

```python
from bot.database.repositories import UserRepository, PostRepository, ReactionRepository

# User operations
user_repo = UserRepository(session)
user, created = await user_repo.get_or_create(telegram_id, username, display_name)
await user_repo.update_karma_total(telegram_id, karma_delta)

# Post operations
post_repo = PostRepository(session)
post = await post_repo.create(message_id, chat_id, author_id, linkedin_url)
posts = await post_repo.get_user_posts_in_period(user_id, days=7)

# Reaction operations
reaction_repo = ReactionRepository(session)
reaction = await reaction_repo.add_reaction(post_id, user_id)
removed = await reaction_repo.remove_reaction(post_id, user_id)
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `pytest`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [aiogram](https://docs.aiogram.dev/) - Modern Telegram Bot framework
- Database management with [SQLAlchemy](https://www.sqlalchemy.org/)
- Testing with [pytest](https://pytest.org/)
