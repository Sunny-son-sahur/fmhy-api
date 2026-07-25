#!/bin/bash

# Setup automatic updates for FMHY API
# This script will install the cron job for daily updates

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPDATE_SCRIPT="$SCRIPT_DIR/update.sh"

echo "=== FMHY Auto-Update Setup ==="
echo ""

# Check if update script exists
if [ ! -f "$UPDATE_SCRIPT" ]; then
    echo "Error: update.sh not found"
    exit 1
fi

# Make sure update script is executable
chmod +x "$UPDATE_SCRIPT"

# Add cron job (daily at 3 AM)
CRON_JOB="0 3 * * * $UPDATE_SCRIPT"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$UPDATE_SCRIPT"; then
    echo "Cron job already exists."
else
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Cron job installed successfully."
fi

echo ""
echo "Current crontab:"
crontab -l 2>/dev/null || echo "No crontab entries."
echo ""
echo "The database will update automatically every day at 3 AM."
echo "You can also run updates manually with: ./update.sh"
