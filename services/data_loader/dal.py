# data_loader/dal.py
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pymongo import AsyncMongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError

from .models import SoldierCreate, SoldierUpdate


class DataLoader:
    """
    קלאס זה הוא המומחה שלנו ל-MongoDB.
    הוא מקבל את פרטי החיבור מבחוץ ואינו תלוי ישירות במשתני סביבה.
    """

    def __init__(self, mongo_uri: str, db_name: str, collection_name: str):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client: Optional[AsyncMongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None

    async def connect(self):
        """יוצר חיבור א-סינכרוני ל-MongoDB ומאתחל נתונים אם צריך."""
        try:
            self.client = AsyncMongoClient(
                self.mongo_uri, serverSelectionTimeoutMS=5000
            )
            await self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            print("Successfully connected to MongoDB.")
            await self._setup_indexes()
        except PyMongoError as e:
            print(f"!!! DATABASE CONNECTION FAILED !!!")
            print(f"Error details: {e}")
            self.client = None
            self.db = None
            self.collection = None

    async def _setup_indexes(self):
        """יוצר אינדקס ייחודי על השדה ID כדי למנוע כפילויות."""
        if self.collection is not None:
            await self.collection.create_index("ID", unique=True)
            print("Unique index on 'ID' field ensured.")

    def disconnect(self):
        """סוגר את החיבור למסד הנתונים."""
        if self.client:
            self.client.close()

    async def get_all_data(self) -> List[Dict[str, Any]]:
        """שולף את כל המסמכים. זורק RuntimeError אם אין חיבור."""
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")

        items: List[Dict[str, Any]] = []
        async for item in self.collection.find({}):
            item["_id"] = str(item["_id"])
            items.append(item)
        return items

    async def get_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """שולף מסמך בודד. זורק RuntimeError אם אין חיבור."""
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")

        item = await self.collection.find_one({"ID": item_id})
        if item:
            item["_id"] = str(item["_id"])
        return item

    async def create_item(self, item: SoldierCreate) -> Dict[str, Any]:
        """יוצר מסמך חדש. זורק שגיאות במקרה של כשל."""
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")
        try:
            item_dict = item.model_dump()
            insert_result = await self.collection.insert_one(item_dict)
            created_item = await self.collection.find_one(
                {"_id": insert_result.inserted_id}
            )
            if created_item:
                created_item["_id"] = str(created_item["_id"])
            return created_item
        except DuplicateKeyError:
            raise ValueError(f"Item with ID {item.ID} already exists.")

    async def update_item(
        self, item_id: int, item_update: SoldierUpdate
    ) -> Optional[Dict[str, Any]]:
        """מעדכן מסמך קיים. זורק RuntimeError אם אין חיבור."""
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")

        update_data = item_update.model_dump(exclude_unset=True)

        if not update_data:
            return await self.get_item_by_id(item_id)

        result = await self.collection.find_one_and_update(
            {"ID": item_id},
            {"$set": update_data},
            return_document=True,
        )
        if result:
            result["_id"] = str(result["_id"])
        return result

    async def delete_item(self, item_id: int) -> bool:
        """מוחק מסמך. זורק RuntimeError אם אין חיבור."""
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")

        delete_result = await self.collection.delete_one({"ID": item_id})
        return delete_result.deleted_count > 0
