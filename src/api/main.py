import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.core.config import settings

from src.db.database import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure media directory exists
    os.makedirs("media", exist_ok=True)
    yield
    await engine.dispose()

app = FastAPI(title="Gymmini", lifespan=lifespan)

# Serve media files
app.mount("/media", StaticFiles(directory="media"), name="media")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
