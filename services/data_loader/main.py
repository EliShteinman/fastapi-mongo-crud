# data_loader/main.py
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, status

from . import models
from .crud import items
from .dependencies import data_loader


@asynccontextmanager
async def lifespan(app: FastAPI):
    # בעליית השרת:
    print("Application startup: connecting to database...")
    await data_loader.connect()
    yield
    # בכיבוי השרת:
    print("Application shutdown: disconnecting from database...")
    data_loader.disconnect()


# יצירת אפליקציית FastAPI
app = FastAPI(
    lifespan=lifespan,
    title="FastAPI MongoDB CRUD Service",
    version="2.0",
    description="A microservice for managing Soldiers, deployed on OpenShift.",
)
app.include_router(items.router)


@app.get("/")
def health_check_endpoint():
    """נקודת קצה לבדיקת תקינות."""
    return {"status": "ok"}
