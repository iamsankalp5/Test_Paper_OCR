"""
Reference document management service.
"""
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from app.config.logging_config import get_logger
from app.services.database_service import DatabaseService

logger = get_logger(__name__)


class ReferenceService:
    """Handles reference document operations."""
    
    def __init__(self, db: DatabaseService):
        """Initialize reference service."""
        self.db = db
        self.collection: AsyncIOMotorCollection = db.db['references']
        logger.info("ReferenceService initialized")
    
    async def create_reference(self, reference_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new reference document.
        
        Args:
            reference_data: Reference data dictionary
            
        Returns:
            Created reference data
        """
        try:
            logger.info(f"Creating reference: {reference_data['reference_id']}")
            await self.collection.insert_one(reference_data)
            logger.info(f"Reference created: {reference_data['reference_id']}")
            return reference_data
        except Exception as e:
            logger.error(f"Reference creation failed: {str(e)}", exc_info=True)
            raise Exception(f"Reference creation failed: {str(e)}")
    
    async def get_reference(self, reference_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve reference by ID.
        
        Args:
            reference_id: Reference identifier
            
        Returns:
            Reference data or None
        """
        try:
            reference = await self.collection.find_one(
                {"reference_id": reference_id},
                {"_id": 0}
            )
            if reference:
                logger.debug(f"Reference retrieved: {reference_id}")
            else:
                logger.warning(f"Reference not found: {reference_id}")
            return reference
        except Exception as e:
            logger.error(f"Reference retrieval failed: {str(e)}", exc_info=True)
            return None
    
    async def update_reference(
        self,
        reference_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update reference data.
        
        Args:
            reference_id: Reference identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated reference data
        """
        try:
            from datetime import datetime
            from pymongo import ReturnDocument
            
            updates['updated_at'] = datetime.utcnow()
            
            logger.info(f"Updating reference: {reference_id}")
            result = await self.collection.find_one_and_update(
                {"reference_id": reference_id},
                {"$set": updates},
                return_document=ReturnDocument.AFTER,
                projection={"_id": 0}
            )
            
            if result:
                logger.info(f"Reference updated: {reference_id}")
            else:
                logger.warning(f"Reference not found for update: {reference_id}")
            
            return result
        except Exception as e:
            logger.error(f"Reference update failed: {str(e)}", exc_info=True)
            raise Exception(f"Reference update failed: {str(e)}")
    
    async def list_references(
        self,
        subject: Optional[str] = None,
        exam_name: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all references with optional filters.
        
        Args:
            subject: Filter by subject
            exam_name: Filter by exam name
            active_only: Only return active references
            
        Returns:
            List of references
        """
        try:
            query = {}
            if active_only:
                query['is_active'] = True
            if subject:
                query['subject'] = subject
            if exam_name:
                query['exam_name'] = exam_name
            
            cursor = self.collection.find(query, {"_id": 0}).sort("created_at", -1)
            references = await cursor.to_list(length=100)
            
            logger.debug(f"Retrieved {len(references)} references")
            return references
        except Exception as e:
            logger.error(f"Reference listing failed: {str(e)}", exc_info=True)
            return []
    
    async def deactivate_reference(self, reference_id: str) -> bool:
        """
        Deactivate a reference document.
        
        Args:
            reference_id: Reference identifier
            
        Returns:
            True if deactivated successfully
        """
        try:
            result = await self.update_reference(reference_id, {"is_active": False})
            return result is not None
        except Exception as e:
            logger.error(f"Reference deactivation failed: {str(e)}")
            return False