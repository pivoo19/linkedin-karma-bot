# Deployment Guide

## Environment Configuration

All configuration should be stored in `.env` file in the project root. Copy the template below and fill in your values:

```bash
# =============================================================================
# TELEGRAM BOT CONFIGURATION
# =============================================================================

# Required: Get your bot token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# For production (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# PostgreSQL configuration (used by docker-compose)
POSTGRES_DB=karma_bot
POSTGRES_USER=karma_bot
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# =============================================================================
# BOT SETTINGS
# =============================================================================

# Default language: ru (Russian) or en (English)
DEFAULT_LANGUAGE=ru

# Number of days to calculate karma (default: 7 days)
DEFAULT_KARMA_PERIOD=7

# Karma points required to become a "veteran" (default: 30)
DEFAULT_VETERAN_THRESHOLD=30

# Karma cost to post a LinkedIn URL (0 = free posting)
DEFAULT_POST_COST=0

# =============================================================================
# DEPLOYMENT CONFIGURATION
# =============================================================================

# SSH configuration for deployment via deploy.sh script

# Remote server user (e.g., root, ubuntu, etc.)
DEPLOY_REMOTE_USER=root

# Remote server hostname or IP
DEPLOY_REMOTE_HOST=your-server.com

# Remote directory path for deployment
DEPLOY_REMOTE_PATH=/root/linkedin-karma-bot

# SSH key path for authentication
DEPLOY_SSH_KEY=~/.ssh/id_rsa
```

## Deployment Steps

### 1. Prepare Local Environment

```bash
# Create .env file with your configuration
cp .env.example .env  # If example exists
# OR manually create .env with the template above
nano .env
```

### 2. Deploy to VPS

#### Option A: Using deploy.sh script (Recommended)

```bash
./deploy.sh
```

The script will:
- Read deployment config from `.env`
- Sync files to remote server via rsync
- Check for conflicts
- Show next steps

#### Option B: Manual deployment

```bash
# Replace variables with your values from .env
rsync -avz --delete \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='logs' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='tests' \
    --exclude='docs' \
    --exclude='*.db' \
    -e "ssh -i ~/.ssh/your_key" \
    ./ your_user@your_host:/path/to/deployment/
```

### 3. On VPS Server

```bash
# SSH to server
ssh -i ~/.ssh/your_key your_user@your_host

# Navigate to project directory
cd /path/to/deployment

# Create .env file on server
nano .env
# Paste your production configuration

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f bot

# Check status
docker-compose ps
```

### 4. Maintenance Commands

```bash
# View logs
docker-compose logs -f bot

# Restart bot
docker-compose restart bot

# Stop services
docker-compose down

# Update deployment
./deploy.sh  # Then restart on server

# Backup database
docker exec karma_bot_postgres pg_dump -U karma_bot karma_bot > backup.sql
```

## Troubleshooting

### Port conflicts
If port 5432 is already in use, change `POSTGRES_PORT` in `.env` to a different port (e.g., 5433).

### Container name conflicts
If containers `karma_bot` or `karma_bot_postgres` already exist:
```bash
docker-compose down
docker-compose up -d
```

### Database connection issues
Check PostgreSQL is running:
```bash
docker-compose ps
docker-compose logs postgres
```

## Security Notes

- Never commit `.env` file to git (it's in `.gitignore`)
- Keep SSH keys secure and use key-based authentication
- Use strong passwords for PostgreSQL
- Regularly backup your database
- Keep Docker images updated
