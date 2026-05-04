"""Base scraper abstract class."""
from abc import ABC, abstractmethod
from typing import List
import httpx
from app.schemas import IntelItem


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""
    
    def __init__(self, source_name: str):
        """Initialize scraper with source name."""
        self.source_name = source_name
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "ThreatIntelSummarizer/1.1 (+https://github.com)"},
        )
    
    @abstractmethod
    async def fetch(self) -> str:
        """Fetch raw data from source."""
        pass
    
    @abstractmethod
    async def parse(self, raw_data: str) -> List[dict]:
        """Parse raw data into structured format."""
        pass
    
    @abstractmethod
    async def normalize(self, parsed_data: List[dict]) -> List[IntelItem]:
        """Normalize parsed data into IntelItem objects."""
        pass
    
    async def scrape(self) -> List[IntelItem]:
        """Execute full scraping pipeline."""
        raw_data = await self.fetch()
        parsed_data = await self.parse(raw_data)
        return await self.normalize(parsed_data)
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
