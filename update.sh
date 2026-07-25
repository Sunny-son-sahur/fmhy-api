#!/bin/bash

# FMHY Auto-Update Script
# This script can be run as a cron job to keep the database up to date
# Example cron job (daily at 3 AM): 0 3 * * * /path/to/fmhy-api/update.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/update.log"
PID_FILE="$SCRIPT_DIR/update.pid"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if update is already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        log "Update already running (PID: $PID). Exiting."
        exit 0
    fi
fi

# Write PID file
echo $$ > "$PID_FILE"

cleanup() {
    rm -f "$PID_FILE"
}
trap cleanup EXIT

log "Starting FMHY database update..."

cd "$SCRIPT_DIR"

# Update wiki content
log "Pulling latest wiki content..."
if [ -d "wiki-content" ]; then
    cd wiki-content
    git pull origin master --quiet
    cd ..
else
    log "Cloning wiki repository..."
    git clone https://github.com/fmhy/FMHY.wiki.git wiki-content --quiet
fi

# Re-parse wiki content
log "Parsing wiki content..."
python3 parser.py

# Re-import to database
log "Importing to database..."
python3 database.py

log "Update completed successfully!"

# Cleanup old logs (keep last 30 days)
find "$LOG_FILE".* -mtime +30 -delete 2>/dev/null || true
mv "$LOG_FILE" "$LOG_FILE.$(date '+%Y%m%d')" 2>/dev/null || true
