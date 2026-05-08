from fastapi import APIRouter

router = APIRouter(
    prefix="/briefs",
    tags=["briefs"]
)

@router.get("/latest")
async def get_latest_brief():
    return {
        "title": "Daily Intelligence Brief",
        "summary": "Threat intelligence system operational.",
        "items": [],
        "critical": 0,
        "high": 0,
        "sources": 0
    }
