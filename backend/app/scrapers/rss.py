"""RSS feed scraper for security blogs."""
from typing import List
from datetime import datetime
from app.scrapers.base import BaseScraper
from app.schemas import IntelItem
import feedparser


class RSSScraper(BaseScraper):
    """Generic RSS feed scraper."""
    
    def __init__(self, source_name: str, feed_url: str):
        super().__init__(source_name)
        self.feed_url = feed_url
    
    async def fetch(self) -> str:
        """Fetch RSS feed."""
        response = await self.client.get(self.feed_url)
        response.raise_for_status()
        return response.text
    
    async def parse(self, raw_data: str) -> List[dict]:
        """Parse RSS/Atom feed."""
        feed = feedparser.parse(raw_data)
        return feed.entries[:10]  # Limit to 10 most recent
    
    async def normalize(self, parsed_data: List[dict]) -> List[IntelItem]:
        """Normalize RSS entries to IntelItem format."""
        items = []
        for entry in parsed_data:
            title = entry.get("title", "No Title")
            link = entry.get("link", "")
            summary = entry.get("summary", entry.get("description", ""))
            
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            published_dt = datetime(*published[:6]) if published else None
            
            severity = self._detect_severity(title, summary)
            
            items.append(IntelItem(
                title=title,
                url=link,
                source=self.source_name,
                published_at=published_dt,
                raw_text=f"{title}. {summary}",
                severity=severity
            ))
        
        return items
    
    def _detect_severity(self, title: str, summary: str) -> str:
        """Detect severity from content keywords."""
        text = f"{title} {summary}".lower()
        
        if any(kw in text for kw in ["critical", "zero-day", "0-day", "ransomware", "breach"]):
            return "CRITICAL"
        elif any(kw in text for kw in ["exploit", "vulnerability", "attack", "malware"]):
            return "HIGH"
        elif any(kw in text for kw in ["patch", "update", "warning"]):
            return "MEDIUM"
        else:
            return "LOW"


class KrebsScraper(RSSScraper):
    """Krebs on Security RSS scraper."""
    def __init__(self):
        super().__init__("Krebs", "https://krebsonsecurity.com/feed/")


class THNScraper(RSSScraper):
    """The Hacker News RSS scraper."""
    def __init__(self):
        super().__init__("TheHackerNews", "https://feeds.feedburner.com/TheHackersNews")


class BleepingComputerScraper(RSSScraper):
    """Bleeping Computer RSS scraper."""
    def __init__(self):
        super().__init__("BleepingComputer", "https://www.bleepingcomputer.com/feed/")


class SchneierScraper(RSSScraper):
    """Schneier on Security Atom scraper."""
    def __init__(self):
        super().__init__("Schneier", "https://www.schneier.com/feed/atom/")
