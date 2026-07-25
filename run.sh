#!/bin/bash

echo "=== FMHY API Setup ==="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Parse wiki data
echo ""
echo "Parsing FMHY wiki data..."
python3 parser.py

# Initialize database and import data
echo ""
echo "Setting up database..."
python3 database.py

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Starting FMHY API server on http://localhost:8000"
echo ""
echo "API Endpoints:"
echo "  GET /                    - API info"
echo "  GET /api/search          - Search resources"
echo "  GET /api/categories      - List all categories"
echo "  GET /api/subcategories   - List subcategories"
echo "  GET /api/resource/{id}   - Get resource by ID"
echo "  GET /api/stats           - Database statistics"
echo "  GET /api/random          - Get random resource"
echo ""
echo "Examples:"
echo "  curl http://localhost:8000/api/search?q=anime"
echo "  curl http://localhost:8000/api/search?category=streaming"
echo "  curl http://localhost:8000/api/categories"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 main.py
