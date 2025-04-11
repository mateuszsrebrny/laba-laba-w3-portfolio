from fastapi import FastAPI

from app.api import router as api_router
from app.ui import router as ui_router

app = FastAPI()
app.include_router(ui_router)
app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "components": {"api": "healthy", "ui": "healthy"}}
