from fastapi import APIRouter

router = APIRouter(
    prefix="/intel",
    tags=["intel"]
)

@router.get("/")
async def intel_root():
    return {"message": "Intel router working"}

@router.post("/scrape")
async def scrape_intel():
    return {
        "status": "success",
        "message": "Scrape endpoint working"
    }
@router.get("/stats")
async def stats():
    return {
        "items_collected": 0,
        "critical": 0,
        "high": 0,
        "sources_active": 0
    }
