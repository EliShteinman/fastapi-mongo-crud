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
    version="1.0",
    description="A microservice for managing items, deployed on OpenShift.",
)
app.include_router(items.router)


@app.get(
    "/data",
    response_model=List[models.OriginalItem],
    summary="Get all data (Original Endpoint)",
    tags=["Original Requirement"],
)
async def get_data_endpoint():
    """
    זוהי נקודת הקצה שנדרשה במבחן.
    היא כוללת טיפול בשגיאות שיכולות לחזור משכבת ה-DAL.
    """

    try:
        all_items = await data_loader.get_all_data()
        return all_items
    except RuntimeError as e:
        # אם ה-DAL זורק שגיאת "אין חיבור", נחזיר שגיאת HTTP 503
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e}",
        )
    except Exception as e:
        # טיפול בשגיאות לא צפויות אחרות
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}",
        )


@app.get("/")
def health_check_endpoint():
    """נקודת קצה לבדיקת תקינות."""
    return {"status": "ok"}
