import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import contextmanager

DATABASE_PATH = "fmhy.db"

def init_db():
    """Initialize the database with the proper schema"""
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                subcategory TEXT NOT NULL,
                is_recommended BOOLEAN DEFAULT 0,
                discord TEXT,
                github TEXT,
                telegram TEXT,
                status TEXT,
                extra_links TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE
            )
        """)
        
        db.execute("CREATE INDEX IF NOT EXISTS idx_category ON resources(category)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_subcategory ON resources(subcategory)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_recommended ON resources(is_recommended)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_name ON resources(name)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_url ON resources(url)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_tag ON tags(tag)")
        
        db.commit()

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def import_from_json(json_path: str):
    """Import resources from JSON file into database"""
    with open(json_path, 'r', encoding='utf-8') as f:
        resources = json.load(f)
    
    with get_db() as db:
        # Clear existing data
        db.execute("DELETE FROM tags")
        db.execute("DELETE FROM resources")
        
        for resource in resources:
            cursor = db.execute("""
                INSERT INTO resources (name, url, description, category, subcategory, 
                                     is_recommended, discord, github, telegram, status, extra_links)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                resource['name'],
                resource['url'],
                resource['description'],
                resource['category'],
                resource['subcategory'],
                resource['is_recommended'],
                resource.get('discord'),
                resource.get('github'),
                resource.get('telegram'),
                resource.get('status'),
                json.dumps(resource.get('extra_links', {}))
            ))
            
            resource_id = cursor.lastrowid
            
            # Insert tags
            for tag in resource.get('tags', []):
                db.execute("""
                    INSERT INTO tags (resource_id, tag)
                    VALUES (?, ?)
                """, (resource_id, tag))
        
        db.commit()
        print(f"Imported {len(resources)} resources into database")

def search_resources(query: str = None, category: str = None, subcategory: str = None, 
                    recommended_only: bool = False, tag: str = None, 
                    has_discord: bool = None, has_github: bool = None, 
                    has_telegram: bool = None, has_status: bool = None,
                    sort_by: str = "name", sort_order: str = "asc",
                    limit: int = 50, offset: int = 0) -> Dict:
    """Search resources with various filters"""
    with get_db() as db:
        sql = "SELECT r.* FROM resources r"
        count_sql = "SELECT COUNT(*) as total FROM resources r"
        conditions = []
        params = []
        joins = []
        
        if query:
            joins.append("LEFT JOIN tags t ON r.id = t.resource_id")
            conditions.append("(r.name LIKE ? OR r.description LIKE ? OR t.tag LIKE ?)")
            query_param = f"%{query}%"
            params.extend([query_param, query_param, query_param])
        
        if category:
            conditions.append("r.category = ?")
            params.append(category)
        
        if subcategory:
            conditions.append("r.subcategory = ?")
            params.append(subcategory)
        
        if recommended_only:
            conditions.append("r.is_recommended = 1")
        
        if tag:
            if not any("LEFT JOIN tags t" in j for j in joins):
                joins.append("LEFT JOIN tags t ON r.id = t.resource_id")
            conditions.append("t.tag = ?")
            params.append(tag)
        
        if has_discord is not None:
            if has_discord:
                conditions.append("r.discord IS NOT NULL AND r.discord != ''")
            else:
                conditions.append("(r.discord IS NULL OR r.discord = '')")
        
        if has_github is not None:
            if has_github:
                conditions.append("r.github IS NOT NULL AND r.github != ''")
            else:
                conditions.append("(r.github IS NULL OR r.github = '')")
        
        if has_telegram is not None:
            if has_telegram:
                conditions.append("r.telegram IS NOT NULL AND r.telegram != ''")
            else:
                conditions.append("(r.telegram IS NULL OR r.telegram = '')")
        
        if has_status is not None:
            if has_status:
                conditions.append("r.status IS NOT NULL AND r.status != ''")
            else:
                conditions.append("(r.status IS NULL OR r.status = '')")
        
        # Build JOIN clause
        if joins:
            sql += " " + " ".join(joins)
            count_sql += " " + " ".join(joins)
        
        # Build WHERE clause
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
            sql += where_clause
            count_sql += where_clause
        
        # Get total count
        total = db.execute(count_sql, params).fetchone()['total']
        
        # Build ORDER BY clause
        valid_sort_fields = ["name", "category", "subcategory", "created_at"]
        if sort_by not in valid_sort_fields:
            sort_by = "name"
        
        valid_sort_orders = ["asc", "desc"]
        if sort_order not in valid_sort_orders:
            sort_order = "asc"
        
        # Add GROUP BY for tag queries
        if any("LEFT JOIN tags t" in j for j in joins):
            sql += " GROUP BY r.id"
        
        sql += f" ORDER BY r.{sort_by} {sort_order.upper()}"
        
        # Add LIMIT and OFFSET
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = db.execute(sql, params).fetchall()
        resources = [dict(row) for row in rows]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "resources": resources
        }

def get_categories() -> List[Dict]:
    """Get all categories with resource counts"""
    with get_db() as db:
        rows = db.execute("""
            SELECT category, COUNT(*) as count
            FROM resources
            GROUP BY category
            ORDER BY count DESC
        """).fetchall()
        return [dict(row) for row in rows]

def get_subcategories(category: str = None) -> List[Dict]:
    """Get subcategories, optionally filtered by category"""
    with get_db() as db:
        if category:
            rows = db.execute("""
                SELECT subcategory, COUNT(*) as count
                FROM resources
                WHERE category = ?
                GROUP BY subcategory
                ORDER BY count DESC
            """, (category,)).fetchall()
        else:
            rows = db.execute("""
                SELECT category, subcategory, COUNT(*) as count
                FROM resources
                GROUP BY category, subcategory
                ORDER BY category, count DESC
            """).fetchall()
        return [dict(row) for row in rows]

def get_resource_by_id(resource_id: int) -> Optional[Dict]:
    """Get a single resource by ID"""
    with get_db() as db:
        row = db.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()
        if row:
            resource = dict(row)
            # Get tags
            tags = db.execute("SELECT tag FROM tags WHERE resource_id = ?", (resource_id,)).fetchall()
            resource['tags'] = [t['tag'] for t in tags]
            return resource
        return None

def get_stats() -> Dict:
    """Get database statistics"""
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) as count FROM resources").fetchone()['count']
        recommended = db.execute("SELECT COUNT(*) as count FROM resources WHERE is_recommended = 1").fetchone()['count']
        categories = db.execute("SELECT COUNT(DISTINCT category) as count FROM resources").fetchone()['count']
        subcategories = db.execute("SELECT COUNT(DISTINCT subcategory) as count FROM resources").fetchone()['count']
        tags = db.execute("SELECT COUNT(DISTINCT tag) as count FROM tags").fetchone()['count']
        with_discord = db.execute("SELECT COUNT(*) as count FROM resources WHERE discord IS NOT NULL AND discord != ''").fetchone()['count']
        with_github = db.execute("SELECT COUNT(*) as count FROM resources WHERE github IS NOT NULL AND github != ''").fetchone()['count']
        with_telegram = db.execute("SELECT COUNT(*) as count FROM resources WHERE telegram IS NOT NULL AND telegram != ''").fetchone()['count']
        
        return {
            'total_resources': total,
            'recommended_resources': recommended,
            'categories': categories,
            'subcategories': subcategories,
            'unique_tags': tags,
            'with_discord': with_discord,
            'with_github': with_github,
            'with_telegram': with_telegram
        }

def get_tags(limit: int = 50) -> List[Dict]:
    """Get all tags with resource counts"""
    with get_db() as db:
        rows = db.execute("""
            SELECT tag, COUNT(*) as count
            FROM tags
            GROUP BY tag
            ORDER BY count DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]

def get_random_resource(category: str = None, subcategory: str = None) -> Optional[Dict]:
    """Get a random resource"""
    with get_db() as db:
        sql = "SELECT * FROM resources WHERE 1=1"
        params = []
        
        if category:
            sql += " AND category = ?"
            params.append(category)
        
        if subcategory:
            sql += " AND subcategory = ?"
            params.append(subcategory)
        
        sql += " ORDER BY RANDOM() LIMIT 1"
        
        row = db.execute(sql, params).fetchone()
        if row:
            return dict(row)
        return None

if __name__ == "__main__":
    init_db()
    import_from_json("fmhy_data.json")
    print("\nDatabase stats:")
    stats = get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
