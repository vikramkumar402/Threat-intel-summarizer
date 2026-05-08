from fastapi import FastAPI
from app.routers.intel import router as intel_router

app = FastAPI()

app.include_router(intel_router)

@app.get("/")
async def root():
    return {"message": "API running"}
