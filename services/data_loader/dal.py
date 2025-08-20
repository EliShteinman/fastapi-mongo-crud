# services/data_loader/dal.py
import logging
from typing import Any, Dict, List, Optional

from pymongo import AsyncMongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, PyMongoError

from .models import SoldierCreate, SoldierUpdate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """
    This class is our MongoDB expert.
    It receives connection details from an external source and is not
    directly dependent on environment variables.
    """

    def __init__(self, mongo_uri: str, db_name: str, collection_name: str):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client: Optional[AsyncMongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None

    async def connect(self):
        """Creates an asynchronous connection to MongoDB and sets up indexes if needed."""
        try:
            self.client = AsyncMongoClient(
                self.mongo_uri, serverSelectionTimeoutMS=5000
            )
            await self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            logger.info("Successfully connected to MongoDB.")
            await self._setup_indexes()
        except PyMongoError as e:
            logger.error(f"DATABASE CONNECTION FAILED: {e}")
            self.client = None
            self.db = None
            self.collection = None

    async def _setup_indexes(self):
        """Creates a unique index on the 'ID' field to prevent duplicates."""
        if self.collection is not None:
            try:
                await self.collection.create_index("ID", unique=True)
                logger.info("Unique index on 'ID' field ensured.")
            except PyMongoError as e:
                logger.error(f"Failed to create index: {e}")

    def disconnect(self):
        """Closes the connection to the database."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB.")

    async def get_all_data(self) -> List[Dict[str, Any]]:
        """Retrieves all documents. Raises RuntimeError if not connected."""
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")

        try:
            items: List[Dict[str, Any]] = []
            async for item in self.collection.find({}):
                item["_id"] = str(item["_id"])
                items.append(item)
            logger.info(f"Retrieved {len(items)} soldiers from database.")
            return items
        except PyMongoError as e:
            logger.error(f"Error retrieving all data: {e}")
            raise RuntimeError(f"Database operation failed: {e}")

    async def get_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single document. Raises RuntimeError if not connected."""
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")

        try:
            item = await self.collection.find_one({"ID": item_id})
            if item:
                item["_id"] = str(item["_id"])
                logger.info(f"Retrieved soldier with ID {item_id}.")
            else:
                logger.info(f"No soldier found with ID {item_id}.")
            return item
        except PyMongoError as e:
            logger.error(f"Error retrieving item with ID {item_id}: {e}")
            raise RuntimeError(f"Database operation failed: {e}")

    async def create_item(self, item: SoldierCreate) -> Dict[str, Any]:
        """Creates a new document. Raises specific errors on failure."""
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
                logger.info(f"Successfully created soldier with ID {item.ID}.")
            return created_item
        except DuplicateKeyError:
            logger.warning(f"Attempt to create duplicate soldier with ID {item.ID}.")
            raise ValueError(f"Item with ID {item.ID} already exists.")
        except PyMongoError as e:
            logger.error(f"Error creating item: {e}")
            raise RuntimeError(f"Database operation failed: {e}")

    async def update_item(
        self, item_id: int, item_update: SoldierUpdate
    ) -> Optional[Dict[str, Any]]:
        """Updates an existing document. Raises RuntimeError if not connected."""
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")

        try:
            update_data = item_update.model_dump(exclude_unset=True)

            if not update_data:
                logger.info(f"No fields to update for soldier ID {item_id}.")
                return await self.get_item_by_id(item_id)

            result = await self.collection.find_one_and_update(
                {"ID": item_id},
                {"$set": update_data},
                return_document=True,
            )
            if result:
                result["_id"] = str(result["_id"])
                logger.info(f"Successfully updated soldier with ID {item_id}.")
            else:
                logger.info(f"No soldier found to update with ID {item_id}.")
            return result
        except PyMongoError as e:
            logger.error(f"Error updating item with ID {item_id}: {e}")
            raise RuntimeError(f"Database operation failed: {e}")

    async def delete_item(self, item_id: int) -> bool:
        """Deletes a document. Raises RuntimeError if not connected."""
        if self.collection is None:
            raise RuntimeError("Database connection is not available.")

        try:
            delete_result = await self.collection.delete_one({"ID": item_id})
            success = delete_result.deleted_count > 0
            if success:
                logger.info(f"Successfully deleted soldier with ID {item_id}.")
            else:
                logger.info(f"No soldier found to delete with ID {item_id}.")
            return success
        except PyMongoError as e:
            logger.error(f"Error deleting item with ID {item_id}: {e}")
            raise RuntimeError(f"Database operation failed: {e}")
