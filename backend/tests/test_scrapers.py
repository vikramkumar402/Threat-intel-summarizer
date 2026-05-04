"""Tests for scrapers."""
import pytest
from datetime import datetime
from app.scrapers.nvd import NVDScraper
from app.scrapers.cisa import CISAScraper
from app.scrapers.rss import KrebsScraper


@pytest.mark.asyncio
async def test_nvd_scraper_normalize():
    """Test NVD scraper normalization."""
    scraper = NVDScraper()
    
    mock_data = [{
        "cve": {
            "id": "CVE-2024-0001",
            "descriptions": [{"value": "Test vulnerability"}],
            "published": "2024-01-01T00:00:00.000Z",
            "metrics": {
                "cvssMetricV31": [{
                    "cvssData": {"baseScore": 9.8}
                }]
            }
        }
    }]
    
    items = await scraper.normalize(mock_data)
    
    assert len(items) == 1
    assert items[0].source == "NVD"
    assert items[0].severity == "CRITICAL"
    assert "CVE-2024-0001" in items[0].title
    
    await scraper.close()


@pytest.mark.asyncio
async def test_cisa_scraper_normalize():
    """Test CISA scraper normalization."""
    scraper = CISAScraper()
    
    mock_data = [{
        "cveID": "CVE-2024-0002",
        "vendorProject": "TestVendor",
        "product": "TestProduct",
        "vulnerabilityName": "Test Vuln",
        "shortDescription": "Test description",
        "dateAdded": "2024-01-01"
    }]
    
    items = await scraper.normalize(mock_data)
    
    assert len(items) == 1
    assert items[0].source == "CISA"
    assert items[0].severity == "CRITICAL"
    assert "EXPLOITED" in items[0].title
    
    await scraper.close()


@pytest.mark.asyncio
async def test_rss_scraper_severity_detection():
    """Test RSS scraper severity detection."""
    scraper = KrebsScraper()
    
    assert scraper._detect_severity("Critical zero-day", "") == "CRITICAL"
    assert scraper._detect_severity("New exploit found", "") == "HIGH"
    assert scraper._detect_severity("Patch released", "") == "MEDIUM"
    assert scraper._detect_severity("General news", "") == "LOW"
    
    await scraper.close()
