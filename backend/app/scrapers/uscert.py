"""US-CERT alerts scraper."""
from typing import List
from datetime import datetime
from app.scrapers.base import BaseScraper
from app.schemas import IntelItem
import feedparser


class USCERTScraper(BaseScraper):
    """Scraper for US-CERT alerts."""
    
    def __init__(self):
        super().__init__("US-CERT")
        self.url = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
    
    async def fetch(self) -> str:
        """Fetch US-CERT alerts feed."""
        response = await self.client.get(self.url)
        response.raise_for_status()
        return response.text
    
    async def parse(self, raw_data: str) -> List[dict]:
        """Parse XML feed."""
        feed = feedparser.parse(raw_data)
        return feed.entries[:10]
    
    async def normalize(self, parsed_data: List[dict]) -> List[IntelItem]:
        """Normalize alerts to IntelItem format."""
        items = []
        for entry in parsed_data:
            title = entry.get("title", "No Title")
            link = entry.get("link", "")
            summary = entry.get("summary", "")
            
            published = entry.get("published_parsed")
            published_dt = datetime(*published[:6]) if published else None
            
            items.append(IntelItem(
                title=title,
                url=link,
                source=self.source_name,
                published_at=published_dt,
                raw_text=f"{title}. {summary}",
                severity="HIGH"  # US-CERT alerts are typically high priority
            ))
        
        return items
