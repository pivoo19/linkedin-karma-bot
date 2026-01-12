#!/bin/bash
# Deployment script for LinkedIn Karma Bot
# Reads deployment configuration from .env file

set -e  # Exit on error

# Load deployment configuration from .env if it exists
if [ -f .env ]; then
    export $(grep -E '^DEPLOY_' .env | xargs)
fi

# Deployment configuration (can be overridden by .env)
REMOTE_USER="${DEPLOY_REMOTE_USER:-root}"
REMOTE_HOST="${DEPLOY_REMOTE_HOST:-}"
REMOTE_PATH="${DEPLOY_REMOTE_PATH:-/root/linkedin-karma-bot}"
SSH_KEY="${DEPLOY_SSH_KEY:-~/.ssh/id_rsa}"

# Validate required variables
if [ -z "$REMOTE_HOST" ]; then
    echo "❌ Error: DEPLOY_REMOTE_HOST is not set"
    echo "   Please add deployment configuration to your .env file"
    echo "   Run the setup command or add these variables manually:"
    echo "   DEPLOY_REMOTE_USER=root"
    echo "   DEPLOY_REMOTE_HOST=your-server.com"
    echo "   DEPLOY_REMOTE_PATH=/root/linkedin-karma-bot"
    echo "   DEPLOY_SSH_KEY=~/.ssh/your_key"
    exit 1
fi

echo "🚀 Starting deployment to VPS..."
echo "   Remote: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"
echo ""

# Expand SSH key path
SSH_KEY_EXPANDED="${SSH_KEY/#\~/$HOME}"

# Check if SSH key exists
if [ ! -f "$SSH_KEY_EXPANDED" ]; then
    echo "❌ SSH key not found: $SSH_KEY_EXPANDED"
    exit 1
fi

# Sync files to VPS
echo "📦 Syncing files..."
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
    --exclude='karma_bot.db' \
    --exclude='*.db' \
    -e "ssh -i $SSH_KEY_EXPANDED" \
    ./ ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/

echo ""
echo "✅ Files synced successfully"
echo ""

# Check for conflicts on remote
echo "🔍 Checking for conflicts..."
ssh -i "$SSH_KEY_EXPANDED" ${REMOTE_USER}@${REMOTE_HOST} << 'EOF'
    # Check if containers with same names exist
    if docker ps -a --format '{{.Names}}' | grep -qE '^(karma_bot|karma_bot_postgres)$'; then
        echo "⚠️  Warning: Containers karma_bot or karma_bot_postgres already exist"
        echo "   They will be stopped and recreated during deployment"
    fi
    
    # Check if port 5432 is in use by other containers
    if docker ps --format '{{.Names}}\t{{.Ports}}' | grep -q ':5432'; then
        echo "⚠️  Warning: Port 5432 is already in use"
        echo "   Make sure to use different POSTGRES_PORT in .env if needed"
    fi
    
    # Check if directory exists
    if [ -d "/root/linkedin-karma-bot" ]; then
        echo "✅ Target directory exists"
    else
        echo "📁 Creating target directory..."
        mkdir -p /root/linkedin-karma-bot
    fi
EOF

echo ""
echo "📋 Next steps:"
echo "   1. SSH to server: ssh -i $SSH_KEY_EXPANDED ${REMOTE_USER}@${REMOTE_HOST}"
echo "   2. Navigate to: cd ${REMOTE_PATH}"
echo "   3. Create .env file with your configuration"
echo "   4. Run: docker-compose up -d"
echo "   5. Check logs: docker-compose logs -f bot"
echo ""
echo "✨ Deployment script completed!"

