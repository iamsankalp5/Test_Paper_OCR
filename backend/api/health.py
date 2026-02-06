"""
Health check endpoint for monitoring and liveness probes.
"""
from fastapi import APIRouter, Depends
from datetime import datetime
from app.config.settings import Settings, get_settings
from app.dependencies import get_database
from app.services.database_service import DatabaseService
from app.core.utils import build_response
from app.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def health_check(
    settings: Settings = Depends(get_settings),
    db: DatabaseService = Depends(get_database)
):
    """
    Health check endpoint.
    
    Returns:
        Health status of the application and its dependencies
    """
    try:
        logger.debug("Health check requested")
        
        # Check database connection
        db_status = "healthy"
        try:
            await db.client.admin.command('ping')
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            logger.error(f"Database health check failed: {str(e)}")
        
        health_data = {
            "application": settings.app_name,
            "version": settings.app_version,
            "status": "healthy" if db_status == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": {
                "database": db_status
            }
        }
        
        return build_response(
            status="success",
            message="Health check completed",
            data=health_data
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return build_response(
            status="error",
            message=f"Health check failed: {str(e)}",
            data=None
        )


@router.get("/readiness")
async def readiness_probe(db: DatabaseService = Depends(get_database)):
    """
    Readiness probe for Kubernetes.
    
    Returns:
        Ready status if all dependencies are available
    """
    try:
        # Check if database is ready
        await db.client.admin.command('ping')
        
        return build_response(
            status="success",
            message="Application is ready",
            data={"ready": True}
        )
        
    except Exception as e:
        logger.error(f"Readiness probe failed: {str(e)}")
        return build_response(
            status="error",
            message="Application is not ready",
            data={"ready": False}
        )


@router.get("/liveness")
async def liveness_probe():
    """
    Liveness probe for Kubernetes.
    
    Returns:
        Alive status
    """
    return build_response(
        status="success",
        message="Application is alive",
        data={"alive": True}
    )