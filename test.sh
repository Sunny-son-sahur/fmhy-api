#!/bin/bash

echo "=== FMHY API Test Suite ==="
echo ""

BASE_URL="http://localhost:8000"

echo "1. Testing root endpoint..."
curl -s "$BASE_URL/" | python3 -c "import sys, json; d = json.load(sys.stdin); print(f'   ✓ API: {d[\"name\"]} v{d[\"version\"]}')"

echo ""
echo "2. Testing categories endpoint..."
curl -s "$BASE_URL/api/categories" | python3 -c "import sys, json; d = json.load(sys.stdin); print(f'   ✓ Found {len(d[\"categories\"])} categories')"

echo ""
echo "3. Testing search endpoint..."
curl -s "$BASE_URL/api/search?q=anime&limit=3" | python3 -c "import sys, json; d = json.load(sys.stdin); print(f'   ✓ Found {d[\"total\"]} results for \"anime\"')"

echo ""
echo "4. Testing random endpoint..."
curl -s "$BASE_URL/api/random" | python3 -c "import sys, json; d = json.load(sys.stdin); print(f'   ✓ Random resource: {d[\"name\"]}')"

echo ""
echo "5. Testing stats endpoint..."
curl -s "$BASE_URL/api/stats" | python3 -c "import sys, json; d = json.load(sys.stdin); print(f'   ✓ Total resources: {d[\"total_resources\"]}')"

echo ""
echo "=== All tests passed! ==="
