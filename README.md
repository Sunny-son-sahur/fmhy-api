# FMHY API

API for Free Media Heck Yeah - The largest collection of free stuff on the internet.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-username/fmhy-api.git
cd fmhy-api

# Run the setup script
./run.sh
```

The API will be available at `http://localhost:8000`

## Auto-Updates

```bash
# Setup automatic daily updates (runs at 3 AM)
./setup-cron.sh

# Or run updates manually
./update.sh
```

## API Endpoints

### Root
```
GET /
```
Returns API information and available endpoints.

### Search Resources
```
GET /api/search
```

**Parameters:**
- `q` (optional): Search query
- `category` (optional): Filter by category (e.g., "Streaming", "Gaming")
- `subcategory` (optional): Filter by subcategory
- `recommended` (optional): Only show recommended resources (default: false)
- `tag` (optional): Filter by tag
- `has_discord` (optional): Filter by has Discord link (true/false)
- `has_github` (optional): Filter by has GitHub link (true/false)
- `has_telegram` (optional): Filter by has Telegram link (true/false)
- `has_status` (optional): Filter by has status page (true/false)
- `sort_by` (optional): Sort field (name, category, subcategory, created_at)
- `sort_order` (optional): Sort order (asc, desc)
- `limit` (optional): Number of results (1-500, default: 50)
- `offset` (optional): Offset for pagination (default: 0)

**Examples:**
```bash
# Search for anime resources
curl "http://localhost:8000/api/search?q=anime&limit=10"

# Get all gaming resources with Discord
curl "http://localhost:8000/api/search?category=Gaming&has_discord=true"

# Get recommended streaming sites
curl "http://localhost:8000/api/search?category=Streaming&recommended=true"

# Search by tag
curl "http://localhost:8000/api/search?tag=4K"
```

### Get Categories
```
GET /api/categories
```
Returns all categories with resource counts.

### Get Subcategories
```
GET /api/subcategories?category=<category>
```
Returns subcategories, optionally filtered by category.

### Get Tags
```
GET /api/tags?limit=<limit>
```
Returns all tags with resource counts.

### Get Resource by ID
```
GET /api/resource/<id>
```
Returns a single resource by its ID.

### Get Random Resource
```
GET /api/random?category=<category>&subcategory=<subcategory>
```
Returns a random resource, optionally filtered by category/subcategory.

### Get Statistics
```
GET /api/stats
```
Returns database statistics.

### Update Database
```
POST /api/update
```
Updates database from FMHY GitHub repo. Returns success/error message.

## Data Structure

Each resource contains:
- `id`: Unique identifier
- `name`: Resource name
- `url`: Resource URL
- `description`: Resource description
- `category`: Main category (e.g., "Streaming", "Gaming")
- `subcategory`: Subcategory (e.g., "Anime Streaming", "Multi-Server")
- `is_recommended`: Whether the resource is recommended (⭐)
- `discord`: Discord link (if available)
- `github`: GitHub link (if available)
- `telegram`: Telegram link (if available)
- `status`: Status page URL (if available)
- `extra_links`: Additional links as JSON
- `tags`: Array of tags

## Categories

- **Adblock**: Adblocking, Privacy, VPNs, Proxies
- **Artificial Intelligence**: Chat Bots, Text Generators, Image Generators
- **Downloading**: Download Sites, Software Sites, Open Directories
- **Educational**: Courses, Documentaries, Learning Resources
- **Gaming**: Download Games, ROMs, Gaming Tools
- **Linux**: Apps, Software Sites, Gaming
- **Misc**: Extensions, Indexes, News, Health, Food, Fun
- **Mobile**: Apps, Jailbreaking, Android Emulators
- **Music**: Stream Audio, Download Audio, Torrent Audio
- **Non-Eng**: International Piracy Sites
- **Reading**: Books, Comics, Magazines, Newspapers
- **Storage**: File Hosting, Cloud Storage
- **Streaming**: Stream Videos, Download Videos, Torrent Videos
- **Torrenting**: Torrent Clients, Torrent Sites, Trackers

## Stats

- **Total Resources**: 1,871
- **Recommended Resources**: 1,277
- **Categories**: 14
- **Subcategories**: 378
- **Unique Tags**: 819

## License

This project is for educational purposes only. Respect the original FMHY project and its contributors.
