"""
Authentication endpoints - Registration and Login.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import timedelta
from app.models.user import (
    UserCreate, UserLogin, UserResponse, Token, UserRole
)
from app.services.database_service import DatabaseService
from app.core.security import hash_password, verify_password, create_access_token
from app.core.auth import get_current_user
from app.config.logging_config import get_logger
from app.dependencies import get_db

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: DatabaseService = Depends(get_db)
):
    """
    Register a new user (teacher or student).
    
    Args:
        user_data: User registration data
        db: Database service
        
    Returns:
        Created user information
        
    Raises:
        HTTPException: If email already exists
    """
    try:
        logger.info(f"Registration attempt for: {user_data.email}")
        
        # await db.connect()
        
        # Check if user already exists
        existing_user = await db.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Create user
        user_dict = user_data.dict()
        user_dict['hashed_password'] = hash_password(user_data.password)
        del user_dict['password']
        
        user_id = await db.create_user(user_dict)
        
        # Get created user
        created_user = await db.get_user_by_id(user_id)
        
        # await db.disconnect()
        
        logger.info(f"User registered successfully: {user_data.email}")
        
        return UserResponse(**created_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: DatabaseService = Depends(get_db)
):
    """
    Login user and return JWT token.
    
    Args:
        credentials: User login credentials
        db: Database service
        
    Returns:
        JWT access token and user information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        logger.info(f"Login attempt for: {credentials.email}")
        
        # await db.connect()
        
        # Get user
        user = await db.get_user_by_email(credentials.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(credentials.password, user['hashed_password']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if active
        if not user.get('is_active', True):
            raise HTTPException(status_code=401, detail="User account is inactive")
        
        # Create access token
        token_data = {
            "user_id": user['user_id'],
            "email": user['email'],
            "role": user['role']
        }
        
        access_token = create_access_token(token_data)
        
        # await db.disconnect()
        
        logger.info(f"Login successful for: {credentials.email}")
        
        return Token(
            access_token=access_token,
            user=UserResponse(**user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return UserResponse(**current_user.dict())