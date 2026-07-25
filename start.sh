#!/bin/bash

# Startup script for deployment platforms
# This script will:
# 1. Clone the FMHY wiki if not present
# 2. Parse the wiki content
# 3. Setup the database
# 4. Filter to streaming only
# 5. Start the API server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== FMHY API Startup ==="

# Check if wiki-content exists, if not clone it
if [ ! -d "wiki-content" ]; then
    echo "Cloning FMHY wiki..."
    git clone https://github.com/fmhy/FMHY.wiki.git wiki-content --quiet
fi

# Check if database exists, if not parse and create it
if [ ! -f "fmhy.db" ]; then
    echo "Setting up database..."
    python3 parser.py
    python3 database.py
    echo "Filtering to streaming only..."
    python3 -c "
import sqlite3
conn = sqlite3.connect('fmhy.db')
conn.execute('DELETE FROM tags WHERE resource_id IN (SELECT id FROM resources WHERE category != \"Streaming\")')
conn.execute('DELETE FROM resources WHERE category != \"Streaming\"')
conn.commit()
conn.close()
print('Filtered to streaming resources only')
"
fi

echo "Starting API server..."
exec python3 main.py
