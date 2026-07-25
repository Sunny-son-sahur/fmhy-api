import re
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class Resource:
    name: str
    url: str
    description: str
    category: str
    subcategory: str
    is_recommended: bool
    tags: List[str]
    discord: Optional[str] = None
    github: Optional[str] = None
    telegram: Optional[str] = None
    status: Optional[str] = None
    extra_links: Dict[str, str] = None

    def __post_init__(self):
        if self.extra_links is None:
            self.extra_links = {}

class FMHYParser:
    def __init__(self, wiki_path: str):
        self.wiki_path = Path(wiki_path)
        self.resources: List[Resource] = []

    def parse_all(self) -> List[Resource]:
        """Parse all markdown files in the wiki directory"""
        md_files = self.wiki_path.glob("*.md")
        
        for md_file in md_files:
            if md_file.name in ["Home.md", "Backups.md", "FMHY-Discord.md", "Stream-Site-Grading.md"]:
                continue
            self.parse_file(md_file)
        
        return self.resources

    def parse_file(self, file_path: Path):
        """Parse a single markdown file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        category = file_path.stem.replace("-", " ")
        lines = content.split('\n')
        
        current_subcategory = "General"
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Detect subcategory headers (## ▷ Name)
            subcat_match = re.match(r'^##\s+▷\s+(.+)$', line)
            if subcat_match:
                current_subcategory = subcat_match.group(1).strip()
                i += 1
                continue
            
            # Detect resource lines (start with * or -)
            if line.startswith('* ') or line.startswith('- '):
                resource = self.parse_resource_line(line, category, current_subcategory)
                if resource:
                    self.resources.append(resource)
            
            i += 1

    def parse_resource_line(self, line: str, category: str, subcategory: str) -> Optional[Resource]:
        """Parse a single resource line"""
        # Remove leading bullet
        line = line[2:].strip()
        
        # Check for recommended star
        is_recommended = line.startswith('⭐')
        if is_recommended:
            line = line[1:].strip()
        
        # Extract main link: **[Name](URL)**
        main_link_match = re.search(r'\*\*\[([^\]]+)\]\(([^)]+)\)\*\*', line)
        if not main_link_match:
            return None
        
        name = main_link_match.group(1)
        url = main_link_match.group(2)
        
        # Get everything after the main link
        after_main = line[main_link_match.end():].strip()
        
        # Split by ' - ' to get description and metadata
        parts = after_main.split(' - ', 1)
        description = parts[0].strip() if parts else ""
        metadata = parts[1].strip() if len(parts) > 1 else ""
        
        # Parse metadata for tags and links
        tags = []
        discord = None
        github = None
        telegram = None
        status = None
        extra_links = {}
        
        # Combine description and metadata for parsing
        full_text = description + " " + metadata if metadata else description
        
        # Extract Discord links
        discord_match = re.search(r'\[Discord\]\(([^)]+)\)', full_text)
        if discord_match:
            discord = discord_match.group(1)
        
        # Extract GitHub links
        github_match = re.search(r'\[GitHub\]\(([^)]+)\)', full_text)
        if github_match:
            github = github_match.group(1)
        
        # Extract Telegram links
        telegram_match = re.search(r'\[Telegram\]\(([^)]+)\)', full_text)
        if telegram_match:
            telegram = telegram_match.group(1)
        
        # Extract Status links
        status_match = re.search(r'\[Status\]\(([^)]+)\)', full_text)
        if status_match:
            status = status_match.group(1)
        
        # Extract other links
        for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', full_text):
            link_name = match.group(1)
            link_url = match.group(2)
            if link_name not in ["Discord", "GitHub", "Telegram", "Status"]:
                # Check if it's a numbered link like [2](url)
                if not link_name.isdigit():
                    extra_links[link_name] = link_url
        
        # Parse tags from metadata
        if metadata:
            # Split by / to get individual items
            items = [item.strip() for item in metadata.split('/')]
            
            for item in items:
                # Skip links (already extracted)
                if re.match(r'\[([^\]]+)\]\(([^)]+)\)', item):
                    continue
                
                # Otherwise it's a tag
                if item and not item.startswith('['):
                    tags.append(item)
        
        return Resource(
            name=name,
            url=url,
            description=description,
            category=category,
            subcategory=subcategory,
            is_recommended=is_recommended,
            tags=tags,
            discord=discord,
            github=github,
            telegram=telegram,
            status=status,
            extra_links=extra_links
        )

def save_to_json(resources: List[Resource], output_path: str):
    """Save resources to JSON file"""
    data = [asdict(r) for r in resources]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(resources)} resources to {output_path}")

if __name__ == "__main__":
    parser = FMHYParser("wiki-content")
    resources = parser.parse_all()
    save_to_json(resources, "fmhy_data.json")
    
    # Print some stats
    categories = {}
    for r in resources:
        if r.category not in categories:
            categories[r.category] = 0
        categories[r.category] += 1
    
    print("\nResources by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")
