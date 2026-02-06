"""
FastAPI application entry point.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import traceback

from app.config.settings import settings
from app.config.logging_config import setup_logging, get_logger
from app.router import api_router
from app.dependencies import get_database, cleanup_services
from app.core.utils import build_response, get_trace_info

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("=" * 80)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info("=" * 80)
    
    try:
        # Initialize database connection
        await get_database()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await cleanup_services()
    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Agentic AI system for automated test paper assessment",
    lifespan=lifespan,
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    }
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to catch all unhandled exceptions.
    
    Args:
        request: FastAPI request object
        exc: Exception that was raised
        
    Returns:
        JSON response with error details
    """
    # Get detailed trace
    trace = get_trace_info()
    error_traceback = traceback.format_exc()
    
    # Log the error
    logger.error(
        f"Unhandled exception at {request.url.path}",
        exc_info=True
    )
    logger.error(f"Traceback:\n{error_traceback}")
    
    # Build error response
    response = build_response(
        status="error",
        message=f"Internal server error: {str(exc)}",
        data=None,
        trace=trace
    )
    
    return JSONResponse(
        status_code=500,
        content=response
    )


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "status": "success",
        "message": f"Welcome to {settings.app_name} API",
        "version": settings.app_version,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )