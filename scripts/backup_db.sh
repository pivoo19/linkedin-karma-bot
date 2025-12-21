#!/bin/bash
# Backup script for PostgreSQL database in Docker container
# Usage: ./backup_db.sh [backup_directory]

set -e  # Exit on error

# Configuration
CONTAINER_NAME="karma_bot_postgres"
DB_NAME="${POSTGRES_DB:-karma_bot}"
DB_USER="${POSTGRES_USER:-karma_bot}"
BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/karma_bot_backup_${TIMESTAMP}.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "🔄 Starting database backup..."
echo "   Container: ${CONTAINER_NAME}"
echo "   Database: ${DB_NAME}"
echo "   Backup file: ${BACKUP_FILE}"

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Error: Container ${CONTAINER_NAME} is not running"
    exit 1
fi

# Create backup using pg_dump
docker exec "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" > "${BACKUP_FILE}"

# Check if backup was successful
if [ $? -eq 0 ] && [ -f "${BACKUP_FILE}" ] && [ -s "${BACKUP_FILE}" ]; then
    # Get file size
    FILE_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "✅ Backup completed successfully!"
    echo "   File: ${BACKUP_FILE}"
    echo "   Size: ${FILE_SIZE}"
    
    # Create a compressed version
    echo "📦 Creating compressed backup..."
    gzip -c "${BACKUP_FILE}" > "${BACKUP_FILE}.gz"
    COMPRESSED_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    echo "   Compressed: ${BACKUP_FILE}.gz (${COMPRESSED_SIZE})"
    
    # Keep only last 10 backups
    echo "🧹 Cleaning old backups (keeping last 10)..."
    ls -t "${BACKUP_DIR}"/karma_bot_backup_*.sql* 2>/dev/null | tail -n +11 | xargs -r rm -f
    
    echo "✨ Backup process completed!"
else
    echo "❌ Error: Backup failed or file is empty"
    rm -f "${BACKUP_FILE}"
    exit 1
fi


