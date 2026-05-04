"""CISA Known Exploited Vulnerabilities scraper."""
from typing import List
from datetime import datetime
from app.scrapers.base import BaseScraper
from app.schemas import IntelItem
import json


class CISAScraper(BaseScraper):
    """Scraper for CISA KEV catalog."""
    
    def __init__(self):
        super().__init__("CISA")
        self.url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    
    async def fetch(self) -> str:
        """Fetch KEV data from CISA."""
        response = await self.client.get(self.url)
        response.raise_for_status()
        return response.text
    
    async def parse(self, raw_data: str) -> List[dict]:
        """Parse JSON response."""
        data = json.loads(raw_data)
        vulnerabilities = data.get("vulnerabilities", [])
        return vulnerabilities[:20]  # Limit to recent 20
    
    async def normalize(self, parsed_data: List[dict]) -> List[IntelItem]:
        """Normalize KEV data to IntelItem format."""
        items = []
        for vuln in parsed_data:
            cve_id = vuln.get("cveID", "UNKNOWN")
            vendor = vuln.get("vendorProject", "")
            product = vuln.get("product", "")
            name = vuln.get("vulnerabilityName", "")
            description = vuln.get("shortDescription", "")
            
            date_added = vuln.get("dateAdded")
            published_dt = datetime.fromisoformat(date_added) if date_added else None
            
            items.append(IntelItem(
                title=f"{cve_id} - {vendor} {product} - EXPLOITED",
                url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                source=self.source_name,
                published_at=published_dt,
                raw_text=f"{cve_id} ({vendor} {product}): {name}. {description}",
                severity="CRITICAL"  # All KEV items are critical
            ))
        
        return items
