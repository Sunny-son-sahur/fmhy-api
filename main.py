from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import uvicorn

from database import (
    init_db, get_categories, get_subcategories, 
    search_resources, get_resource_by_id, get_stats,
    get_tags, get_random_resource
)

app = FastAPI(
    title="FMHY API",
    description="API for Free Media Heck Yeah - The largest collection of free stuff on the internet",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/")
async def root():
    return {
        "name": "FMHY API",
        "version": "1.0.0",
        "description": "API for Free Media Heck Yeah resource collection",
        "endpoints": {
            "search": "/api/search",
            "categories": "/api/categories",
            "subcategories": "/api/subcategories",
            "tags": "/api/tags",
            "resource": "/api/resource/{id}",
            "random": "/api/random",
            "stats": "/api/stats",
            "update": "/api/update"
        }
    }

@app.get("/api/search")
async def search(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    recommended: bool = Query(False, description="Only show recommended resources"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    has_discord: Optional[bool] = Query(None, description="Filter by has Discord link"),
    has_github: Optional[bool] = Query(None, description="Filter by has GitHub link"),
    has_telegram: Optional[bool] = Query(None, description="Filter by has Telegram link"),
    has_status: Optional[bool] = Query(None, description="Filter by has status page"),
    sort_by: str = Query("name", description="Sort field (name, category, subcategory, created_at)"),
    sort_order: str = Query("asc", description="Sort order (asc, desc)"),
    limit: int = Query(50, ge=1, le=500, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    return search_resources(
        query=q,
        category=category,
        subcategory=subcategory,
        recommended_only=recommended,
        tag=tag,
        has_discord=has_discord,
        has_github=has_github,
        has_telegram=has_telegram,
        has_status=has_status,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )

@app.get("/api/categories")
async def categories():
    return {"categories": get_categories()}

@app.get("/api/subcategories")
async def subcategories(category: Optional[str] = None):
    return {"subcategories": get_subcategories(category)}

@app.get("/api/resource/{resource_id}")
async def resource(resource_id: int):
    resource = get_resource_by_id(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource

@app.get("/api/stats")
async def stats():
    return get_stats()

@app.get("/api/tags")
async def tags(limit: int = Query(50, ge=1, le=500, description="Number of tags to return")):
    return {"tags": get_tags(limit)}

@app.post("/api/update")
async def update_database():
    """Update database from FMHY GitHub repo"""
    import subprocess
    import sys
    from pathlib import Path
    
    try:
        # Update wiki content
        wiki_path = Path("wiki-content")
        if wiki_path.exists():
            subprocess.run(
                ["git", "pull"],
                cwd=wiki_path,
                capture_output=True,
                text=True,
                check=True
            )
        
        # Re-parse and import
        subprocess.run(
            [sys.executable, "parser.py"],
            capture_output=True,
            text=True,
            check=True
        )
        
        subprocess.run(
            [sys.executable, "database.py"],
            capture_output=True,
            text=True,
            check=True
        )
        
        return {"message": "Database updated successfully", "status": "success"}
    
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Update failed: {e.stderr or str(e)}"
        )

@app.get("/api/random")
async def random_resource(
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory")
):
    resource = get_random_resource(category, subcategory)
    if not resource:
        raise HTTPException(status_code=404, detail="No resources found")
    return resource

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
