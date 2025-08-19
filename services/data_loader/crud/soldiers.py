# services/data_loader/crud/soldiers.py
from typing import List

from fastapi import APIRouter, HTTPException, status

# Import the Pydantic models and the shared DAL instance
from .. import models
from ..dependencies import data_loader

# Create an APIRouter instance. Think of it as a "mini-FastAPI" application.
router = APIRouter(
    prefix="/soldiersdb",  # All paths in this router will be prefixed with /soldiersdb
    tags=[
        "Soldiers CRUD"
    ],  # Group these endpoints under "Soldiers CRUD" in the Swagger UI docs
)


# --- CREATE ---
@router.post(
    "/", response_model=models.SoldierInDB, status_code=status.HTTP_201_CREATED
)
async def create_soldier(soldier: models.SoldierCreate):
    """
    Creates a new soldier in the database.
    """
    try:
        created_soldier = await data_loader.create_item(soldier)
        return created_soldier
    except ValueError as e:
        # Catch the duplicate ID error from the DAL and convert it to a 409 Conflict response
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RuntimeError as e:
        # Catch a database connection error from the DAL and convert it to a 503 Service Unavailable response
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


# --- READ (All) ---
@router.get("/", response_model=List[models.SoldierInDB])
async def read_all_soldiers():
    """
    Retrieves all soldiers from the database.
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
    Retrieves a single soldier by their numeric ID.
    """
    try:
        soldier = await data_loader.get_item_by_id(soldier_id)
        if soldier is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Soldier with ID {soldier_id} not found",
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
    Updates an existing soldier by their numeric ID.
    """
    try:
        updated_soldier = await data_loader.update_item(soldier_id, soldier_update)
        if updated_soldier is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Soldier with ID {soldier_id} not found to update",
            )
        return updated_soldier
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


# --- DELETE ---
@router.delete("/{soldier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_soldier(soldier_id: int):
    """
    Deletes an existing soldier by their numeric ID.
    """
    try:
        success = await data_loader.delete_item(soldier_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Soldier with ID {soldier_id} not found to delete",
            )
        # On successful deletion with a 204 status, no response body is returned.
        return
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
