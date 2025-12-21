# VPS Deployment Instructions

## Prerequisites

1. SSH access to VPS server (see `VPS_ACCESS.md`)
2. Docker and Docker Compose installed on the server
3. `.env` file with bot settings

## Conflict Check

Before deployment, check for potential conflicts:
- Other PostgreSQL containers may use port **5432**
- Other containers with similar names

**Important:** Our bot uses:
- Containers: `karma_bot` and `karma_bot_postgres`
- PostgreSQL port: **5433** by default (to avoid conflict with existing PostgreSQL on 5432)

## Quick Deployment

### 1. Locally (from your computer)

```bash
./deploy.sh
```

The script automatically:
- Syncs files to VPS
- Checks for conflicts with existing containers
- Shows next steps

### 2. On the server

After syncing files, connect to the server:

```bash
ssh -i ~/.ssh/your_ssh_key root@your-server.com
cd /root/linkedin-karma-bot
```

### 3. Create `.env` file

```bash
# Copy example and edit
cp .env.example .env
nano .env
```

**Required settings:**
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql+asyncpg://karma_bot:your_password@postgres:5432/karma_bot

# PostgreSQL settings (port 5433 to avoid conflict)
POSTGRES_PORT=5433
POSTGRES_DB=karma_bot
POSTGRES_USER=karma_bot
POSTGRES_PASSWORD=your_secure_password

# Optional settings
DEFAULT_LANGUAGE=ru
DEFAULT_KARMA_PERIOD=7
DEFAULT_VETERAN_THRESHOLD=30
DEFAULT_POST_COST=0
```

### 4. Start the bot

```bash
# Build and start containers
docker-compose up -d

# Check logs
docker-compose logs -f bot

# Check status
docker-compose ps
```

### 5. Verify operation

```bash
# Bot logs
docker-compose logs -f bot

# PostgreSQL logs
docker-compose logs -f postgres

# Container status
docker-compose ps
```

## Bot Update

After code changes:

```bash
# Locally
./deploy.sh

# On server (replace with your actual path)
cd /root/linkedin-karma-bot
docker-compose down
docker-compose up -d --build
docker-compose logs -f bot
```

## Stop and Remove

```bash
# Replace with your actual deployment path
cd /root/linkedin-karma-bot
docker-compose down

# If you need to delete database data
docker-compose down -v
```

## Troubleshooting

### Port 5433 already in use

Change `POSTGRES_PORT` in `.env` to another port (e.g., 5434) and update `DATABASE_URL`:

```env
POSTGRES_PORT=5434
DATABASE_URL=postgresql+asyncpg://karma_bot:password@postgres:5432/karma_bot
```

### Container won't start

```bash
# Check logs
docker-compose logs bot

# Check configuration
docker-compose config

# Recreate containers
docker-compose down
docker-compose up -d --build
```

### Database issues

```bash
# Check PostgreSQL connection
docker-compose exec postgres psql -U karma_bot -d karma_bot

# Run migrations manually
docker-compose exec bot alembic upgrade head
```

## Monitoring

```bash
# Resource usage
docker stats karma_bot karma_bot_postgres

# Container health check
docker-compose ps
```
