"""
Authentication utilities.
"""
from typing import Optional
from fastapi import HTTPException, Depends, Header, Security
from app.models.user import UserInDB, UserRole, TokenData
from app.services.database_service import DatabaseService
from app.core.security import decode_access_token
from app.config.logging_config import get_logger
from app.dependencies import get_db
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = get_logger(__name__)

security = HTTPBearer(
    scheme_name="Bearer",
    description="Enter your JWT token (without 'Bearer' prefix)"
)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: DatabaseService = Depends(get_db)
) -> UserInDB:
    """
    Get current authenticated user from JWT token.
    
    Args:
        authorization: Authorization header with Bearer token
        db: Database service
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    # Extract token from credentials (without "Bearer " prefix)
    token = credentials.credentials
    
    # Decode and validate token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract user_id from token
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Get user from database
    user = await db.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=401,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    logger.debug(f"Authenticated user: {user['email']} ({user['role']})")
    
    return UserInDB(**user)


async def get_current_teacher(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Verify current user is a teacher.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user if teacher
        
    Raises:
        HTTPException: If user is not a teacher
    """
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can access this resource"
        )
    return current_user


async def get_current_student(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Verify current user is a student.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user if student
        
    Raises:
        HTTPException: If user is not a student
    """
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=403,
            detail="Only students can access this resource"
        )
    return current_user