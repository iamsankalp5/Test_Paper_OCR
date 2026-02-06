"""
MongoDB database service for CRUD operations.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import ReturnDocument
from app.config.logging_config import get_logger
from app.config.settings import settings
import uuid

logger = get_logger(__name__)


class DatabaseService:
    """Handles MongoDB operations for job data."""
    
    def __init__(self):
        """Initialize database service."""
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.jobs_collection: Optional[AsyncIOMotorCollection] = None
        logger.info("DatabaseService initialized")

    def _convert_objectid(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert MongoDB ObjectId to string for JSON serialization.
        
        Args:
            doc: MongoDB document
            
        Returns:
            Document with ObjectId converted to string
        """
        if doc and '_id' in doc:
            doc['_id'] = str(doc['_id'])
        return doc

    
    async def connect(self):
        """Establish MongoDB connection."""
        try:
            logger.info(f"Connecting to MongoDB: {settings.mongodb_url}")
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.db = self.client[settings.mongodb_db_name]
            self.jobs_collection = self.db['jobs']
            
            # Verify connection
            await self.client.admin.command('ping')
            logger.info("MongoDB connection established successfully")
            
            # Create indexes
            await self.jobs_collection.create_index("job_id", unique=True)
            await self.jobs_collection.create_index("created_at")
            logger.info("Database indexes created")
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}", exc_info=True)
            raise Exception(f"Database connection failed: {str(e)}")
    
    async def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new job document with automatic timestamp handling.
        """
        try:
            logger.info(f"Creating job: {job_data['job_id']}")

            # ✅ Use IST timezone (UTC + 5:30)
            IST = timezone(timedelta(hours=5, minutes=30))
            
            # Debug: Check if timestamps exist before adding
            logger.info(f"[DEBUG] created_at before auto-add: {job_data.get('created_at')}")
            logger.info(f"[DEBUG] updated_at before auto-add: {job_data.get('updated_at')}")
            
            # Auto-add timestamps if not present
            if "created_at" not in job_data:
                job_data["created_at"] = datetime.now(IST)
                logger.info(f"[DEBUG] Auto-added created_at: {job_data['created_at']}")
            
            if "updated_at" not in job_data:
                job_data["updated_at"] = datetime.now(IST)
                logger.info(f"[DEBUG] Auto-added updated_at: {job_data['updated_at']}")
            
            # Insert into database
            result = await self.jobs_collection.insert_one(job_data)
            logger.info(f"Job created with ID: {result.inserted_id} at {job_data['created_at']}")
            
            # Debug: Verify what was inserted
            inserted_job = await self.jobs_collection.find_one({"job_id": job_data["job_id"]})
            logger.info(f"[DEBUG] Verified in DB - created_at: {inserted_job.get('created_at')}")
            
            return job_data
            
        except Exception as e:
            logger.error(f"Job creation failed: {str(e)}", exc_info=True)
            raise Exception(f"Job creation failed: {str(e)}")
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job data or None if not found
        """
        try:
            job = await self.jobs_collection.find_one({"job_id": job_id}, {"_id": 0})
            if job:
                logger.debug(f"Job retrieved: {job_id}")
            else:
                logger.warning(f"Job not found: {job_id}")
            return job
        except Exception as e:
            logger.error(f"Job retrieval failed: {str(e)}", exc_info=True)
            return None
    
    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update job data with automatic timestamp handling.
        """
        try:
            # ✅ Use IST timezone (UTC + 5:30)
            IST = timezone(timedelta(hours=5, minutes=30))
            updates['updated_at'] = datetime.now(IST)
            
            logger.info(f"Updating job: {job_id} at {updates['updated_at']}")
            
            result = await self.jobs_collection.find_one_and_update(
                {"job_id": job_id},
                {"$set": updates},
                return_document=ReturnDocument.AFTER,
                projection={"_id": 0}
            )
            
            if result:
                logger.info(f"Job updated successfully: {job_id}")
            else:
                logger.warning(f"Job not found for update: {job_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Job update failed: {str(e)}", exc_info=True)
            raise Exception(f"Job update failed: {str(e)}")
    
    async def delete_job(self, job_id: str) -> bool:
        """
        Delete job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.jobs_collection.delete_one({"job_id": job_id})
            deleted = result.deleted_count > 0
            if deleted:
                logger.info(f"Job deleted: {job_id}")
            else:
                logger.warning(f"Job not found for deletion: {job_id}")
            return deleted
        except Exception as e:
            logger.error(f"Job deletion failed: {str(e)}", exc_info=True)
            return False
    
    async def list_jobs(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List jobs with pagination and filtering.
        
        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            filters: Optional filter criteria
            
        Returns:
            List of job documents
        """
        try:
            query = filters or {}
            cursor = self.jobs_collection.find(query, {"_id": 0}).skip(skip).limit(limit)
            jobs = await cursor.to_list(length=limit)
            logger.debug(f"Retrieved {len(jobs)} jobs")
            return jobs
        except Exception as e:
            logger.error(f"Job listing failed: {str(e)}", exc_info=True)
            return []
        
    async def get_jobs_by_query(
        self,
        query: Dict[str, Any],
        limit: int = 50,
        sort_by: str = "created_at",
        sort_order: int = -1  # -1 for descending (newest first)
    ) -> List[Dict[str, Any]]:
        """
        Get jobs by custom query.
        
        Args:
            query: MongoDB query dictionary
            limit: Maximum results
            sort_by: Field to sort by
            sort_order: 1 for ascending, -1 for descending
            
        Returns:
            List of job documents
        """
        try:
            cursor = self.jobs_collection.find(query).sort(sort_by, sort_order).limit(limit)
            jobs = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for job in jobs:
                if '_id' in job:
                    job['_id'] = str(job['_id'])
            
            return jobs
        except Exception as e:
            logger.error(f"Failed to fetch jobs: {str(e)}")
            return []

     # ============================================================
     # USER MANAGEMENT METHODS
     # ============================================================

    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """
        Create a new user.
        
        Args:
            user_data: User data dictionary
            
        Returns:
            Created user ID
        """
        try:
            user_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            user_doc = {
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "is_active": True,
                **user_data
            }
            
            result = await self.db.users.insert_one(user_doc)
            
            logger.info(f"User created: {user_id}")
            return user_id
            
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise


    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            user = await self.db.users.find_one({"user_id": user_id})
            return self._convert_objectid(user) if user else None
        except Exception as e:
            logger.error(f"Failed to get user: {str(e)}")
            return None


    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        try:
            user = await self.db.users.find_one({"email": email})
            return self._convert_objectid(user) if user else None   
        except Exception as e:
            logger.error(f"Failed to get user by email: {str(e)}")
            return None
        
    # ============================================================
    # TEACHER DASHBOARD METHODS
    # ============================================================

    async def get_references_by_teacher(self, teacher_email: str) -> List[Dict[str, Any]]:
        """Get all references uploaded by a teacher."""
        try:
            cursor = self.db.references.find({"teacher_email": teacher_email})
            references = await cursor.to_list(length=100)
            
            return [self._convert_objectid(ref) for ref in references]
        except Exception as e:
            logger.error(f"Failed to get teacher references: {str(e)}")
            return []


    async def count_submissions_for_reference(self, reference_id: str) -> int:
        """Count how many students submitted for this reference."""
        try:
            count = await self.db.jobs.count_documents({"reference_id": reference_id})
            return count
        except Exception as e:
            logger.error(f"Failed to count submissions: {str(e)}")
            return 0


    async def get_submissions_by_reference(self, reference_id: str) -> List[Dict[str, Any]]:
        """Get all student submissions for a reference."""
        try:
            cursor = self.db.jobs.find({"reference_id": reference_id})
            submissions = await cursor.to_list(length=1000)
            return [self._convert_objectid(sub) for sub in submissions]
        except Exception as e:
            logger.error(f"Failed to get submissions: {str(e)}")
            return []


    async def get_reference_by_id(self, reference_id: str) -> Optional[Dict[str, Any]]:
        """Get reference by ID."""
        try:
            reference = await self.db.references.find_one({"reference_id": reference_id})
            return self._convert_objectid(reference) if reference else None
        except Exception as e:
            logger.error(f"Failed to get reference: {str(e)}")
            return None
        
    async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job data or None if not found
        """
        try:
            job = await self.db.jobs.find_one({"job_id": job_id})
            return self._convert_objectid(job) if job else None
        except Exception as e:
            logger.error(f"Failed to get job: {str(e)}")
            return None