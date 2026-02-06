"""
Dependency injection for FastAPI endpoints.
"""
from functools import lru_cache
from typing import AsyncGenerator
from app.config.settings import Settings, get_settings
from app.services.database_service import DatabaseService
from app.services.storage_service import StorageService
from app.services.llm_service import LLMService
from app.services.pdf_service import PDFService
from app.services.vision_service import VisionService
from app.services.notification_service import NotificationService
from app.core.image_preprocessor import ImagePreprocessor
from app.core.ocr_engine import OCREngine
from app.core.answer_parser import AnswerParser
from app.core.assessment_engine import AssessmentEngine
from app.core.feedback_generator import FeedbackGenerator
from app.core.report_generator import ReportGenerator
from app.core.reviewer import Reviewer
from app.core.workflow_manager import WorkflowManager
from app.core.agent_controller import AgentController
from app.config.logging_config import get_logger

logger = get_logger(__name__)

# Global service instances
_db_service: DatabaseService = None
_storage_service: StorageService = None
_llm_service: LLMService = None
_pdf_service: PDFService = None
_vision_service: VisionService = None
_notification_service: NotificationService = None
_agent_controller: AgentController = None


async def get_database() -> DatabaseService:
    """Get database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
        await _db_service.connect()
        logger.info("Database service initialized")
    return _db_service


def get_storage() -> StorageService:
    """Get storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
        logger.info("Storage service initialized")
    return _storage_service


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
        logger.info("LLM service initialized")
    return _llm_service


def get_pdf_service() -> PDFService:
    """Get PDF service instance."""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
        logger.info("PDF service initialized")
    return _pdf_service


def get_vision_service() -> VisionService:
    """Get vision service instance."""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
        logger.info("Vision service initialized")
    return _vision_service


def get_notification_service() -> NotificationService:
    """Get notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
        logger.info("Notification service initialized")
    return _notification_service


def get_agent_controller() -> AgentController:
    """Get agent controller instance."""
    global _agent_controller
    if _agent_controller is None:
        _agent_controller = AgentController()
        logger.info("Agent controller initialized")
    return _agent_controller

# ============================================================
# NEW: Authentication Support Functions
# ============================================================

def get_db_service() -> DatabaseService:
    """
    Get database service instance (synchronous wrapper).
    Used for auth endpoints that need DatabaseService type.
    
    Returns:
        DatabaseService instance
    """
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
        logger.info("Database service initialized")
    return _db_service


def get_storage_service() -> StorageService:
    """
    Get storage service instance.
    Alias for get_storage() for consistency.
    
    Returns:
        StorageService instance
    """
    return get_storage()


async def get_db() -> AsyncGenerator[DatabaseService, None]:
    """
    Get database service with automatic connection management.
    Better for auth endpoints - handles connect/disconnect automatically.
    
    Yields:
        Connected DatabaseService instance
        
    Usage:
        @router.post("/endpoint")
        async def endpoint(db: DatabaseService = Depends(get_db)):
            # db is already connected
            # will auto-disconnect after request
    """
    db = DatabaseService()
    await db.connect()
    try:
        yield db
    finally:
        await db.disconnect()
        logger.debug("Database connection closed for request")


# ============================================================
# Cleanup
# ============================================================

async def cleanup_services():
    """Cleanup all services on shutdown."""
    global _db_service
    if _db_service:
        await _db_service.disconnect()
        logger.info("All services cleaned up")