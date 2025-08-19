from typing import List

from fastapi import APIRouter, HTTPException, status

# מייבאים את המודלים ואת ה-DAL המשותף
from .. import models
from ..dependencies import data_loader

# יוצרים אובייקט APIRouter. חשוב עליו כעל "מיני-אפליקציה" נפרדת.
router = APIRouter(
    prefix="/soldiersdb",  # כל הנתיבים כאן יתחילו אוטומטית ב-/soldiersdb
    tags=["soldiersdb CRUD"],  # שם הקבוצה בתיעוד ה-Swagger
)


# --- CREATE ---
@router.post(
    "/", response_model=models.SoldierInDB, status_code=status.HTTP_201_CREATED
)
async def create_soldier(soldier: models.SoldierCreate):
    """
    יוצר חייל חדש במסד הנתונים.
    """
    try:
        created_soldier = await data_loader.create_item(soldier)
        return created_soldier
    except ValueError as e:
        # תופסים את שגיאת ה-ID הכפול מה-DAL
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


# --- READ (All) ---
@router.get("/", response_model=List[models.SoldierInDB])
async def read_all_soldiers():
    """
    שולף את כל החיילים ממסד הנתונים.
    """
    try:
        return await data_loader.get_all_data()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


# --- READ (Single) ---
@router.get("/{soldier_id}", response_model=models.SoldierInDB)
async def read_soldier_by_id(soldier_id: int):
    """
    שולף פריט בודד לפי ה-ID המספרי שלו.
    """
    try:
        soldier = await data_loader.get_item_by_id(soldier_id)
        if soldier is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {soldier_id} not found",
            )
        return soldier
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


# --- UPDATE ---
@router.put("/{soldier_id}", response_model=models.SoldierInDB)
async def update_soldier(soldier_id: int, soldier_update: models.SoldierUpdate):
    """
    מעדכן חייל קיים לפי ה-ID המספרי שלו.
    """
    try:
        soldier_item = await data_loader.update_item(soldier_id, soldier_update)
        if soldier_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {soldier_id} not found to update",
            )
        return soldier_item
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


# --- DELETE ---
@router.delete("/{soldier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_soldier(soldier_id: int):
    """
    מוחק חייל קיים לפי ה-ID המספרי שלו.
    """
    try:
        success = await data_loader.delete_item(soldier_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {soldier_id} not found to delete",
            )
        # עם סטטוס 204, לא מחזירים גוף תשובה
        return
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
