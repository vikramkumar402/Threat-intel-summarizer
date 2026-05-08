from fastapi import APIRouter

router = APIRouter(
    prefix="/briefs",
    tags=["briefs"]
)

@router.get("/latest")
async def latest_brief():
    return {
        "brief": "No brief yet"
    }
