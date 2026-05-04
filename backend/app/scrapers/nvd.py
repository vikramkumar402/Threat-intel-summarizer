"""NVD CVE feed scraper."""
from typing import List
from datetime import datetime
from app.scrapers.base import BaseScraper
from app.schemas import IntelItem
import json


class NVDScraper(BaseScraper):
    """Scraper for NVD CVE feed."""
    
    def __init__(self):
        super().__init__("NVD")
        self.url = "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=20"
    
    async def fetch(self) -> str:
        """Fetch CVE data from NVD API."""
        response = await self.client.get(self.url)
        response.raise_for_status()
        return response.text
    
    async def parse(self, raw_data: str) -> List[dict]:
        """Parse JSON response."""
        data = json.loads(raw_data)
        return data.get("vulnerabilities", [])
    
    async def normalize(self, parsed_data: List[dict]) -> List[IntelItem]:
        """Normalize CVE data to IntelItem format."""
        items = []
        for vuln in parsed_data:
            cve = vuln.get("cve", {})
            cve_id = cve.get("id", "UNKNOWN")
            
            descriptions = cve.get("descriptions", [])
            description = descriptions[0].get("value", "") if descriptions else ""
            
            metrics = cve.get("metrics", {})
            cvss_v3 = metrics.get("cvssMetricV31", [{}])[0] if metrics.get("cvssMetricV31") else {}
            base_score = cvss_v3.get("cvssData", {}).get("baseScore", 0)
            
            severity = "UNKNOWN"
            if base_score >= 9.0:
                severity = "CRITICAL"
            elif base_score >= 7.0:
                severity = "HIGH"
            elif base_score >= 4.0:
                severity = "MEDIUM"
            elif base_score > 0:
                severity = "LOW"
            
            published = cve.get("published")
            published_dt = datetime.fromisoformat(published.replace("Z", "+00:00")) if published else None
            
            items.append(IntelItem(
                title=f"{cve_id} - CVSS {base_score}",
                url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                source=self.source_name,
                published_at=published_dt,
                raw_text=f"{cve_id}: {description}",
                severity=severity
            ))
        
        return items
