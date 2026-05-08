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
