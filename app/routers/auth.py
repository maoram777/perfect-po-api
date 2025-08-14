from fastapi import APIRouter, Depends, HTTPException, status
from ..auth.jwt import create_access_token, verify_password, get_password_hash, verify_and_upgrade_password
from ..auth.dependencies import get_current_active_user
from ..database import get_database
from ..models.user import User, UserCreate, UserLogin, UserResponse
from bson import ObjectId
from datetime import timedelta, datetime
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user."""
    logger.info(f"Starting user registration for email: {user_data.email}")
    logger.info(f"Registration data: username={user_data.username}, full_name={user_data.full_name}")
    
    try:
        logger.info("Getting database connection...")
        db = get_database()
        logger.info("Database connection established successfully")
        
        # Check if user already exists
        logger.info(f"Checking if email {user_data.email} already exists...")
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            logger.warning(f"Email {user_data.email} already registered")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        logger.info("Email check passed - email is available")
        
        logger.info(f"Checking if username {user_data.username} already exists...")
        existing_username = await db.users.find_one({"username": user_data.username})
        if existing_username:
            logger.warning(f"Username {user_data.username} already taken")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        logger.info("Username check passed - username is available")
        
        # Hash password and create user
        logger.info("Hashing password...")
        hashed_password = get_password_hash(user_data.password)
        logger.info("Password hashed successfully")
        
        logger.info("Preparing user data for database insertion...")
        user_dict = user_data.dict()
        user_dict["hashed_password"] = hashed_password
        user_dict["_id"] = ObjectId()
        user_dict["is_active"] = True
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        
        logger.info(f"User data prepared: {user_dict}")
        
        # Insert user into database
        logger.info("Inserting user into database...")
        result = await db.users.insert_one(user_dict)
        logger.info(f"User inserted successfully with ID: {result.inserted_id}")
        
        user_dict["_id"] = result.inserted_id
        
        # Return user without password
        logger.info("Creating user response...")
        user_response = UserResponse(
            id=str(user_dict["_id"]),
            email=user_dict["email"],
            username=user_dict["username"],
            full_name=user_dict["full_name"],
            is_active=user_dict["is_active"],
            created_at=user_dict["created_at"],
            updated_at=user_dict["updated_at"]
        )
        
        logger.info(f"User registered successfully: {user_data.email} with ID: {result.inserted_id}")
        return user_response
        
    except HTTPException as he:
        logger.warning(f"HTTPException during registration: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error during user registration: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/login")
async def login(user_data: UserLogin):
    """Authenticate user and return JWT token."""
    logger.info(f"Login attempt for email: {user_data.email}")
    
    try:
        logger.info("Getting database connection...")
        db = get_database()
        logger.info("Database connection established successfully")
        
        # Find user by email
        logger.info(f"Searching for user with email: {user_data.email}")
        user = await db.users.find_one({"email": user_data.email})
        if not user:
            logger.warning(f"Login failed: User not found for email {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.info(f"User found: {user['email']}")
        
        # Verify password and potentially upgrade hash
        logger.info("Verifying password...")
        is_valid, new_hash = verify_and_upgrade_password(user_data.password, user["hashed_password"])
        if not is_valid:
            logger.warning(f"Login failed: Invalid password for user {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.info("Password verification successful")
        
        # Update password hash if it was upgraded from bcrypt to argon2
        if new_hash != user["hashed_password"]:
            logger.info("Upgrading password hash from bcrypt to argon2...")
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"hashed_password": new_hash, "updated_at": datetime.utcnow()}}
            )
            logger.info("Password hash upgraded successfully")
        
        # Check if user is active
        logger.info("Checking if user is active...")
        if not user.get("is_active", True):
            logger.warning(f"Login failed: Inactive user {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        logger.info("User is active")
        
        # Create access token
        logger.info("Creating access token...")
        access_token = create_access_token(
            data={"sub": str(user["_id"])}
        )
        logger.info("Access token created successfully")
        
        logger.info(f"User logged in successfully: {user['email']}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user["_id"]),
                "email": user["email"],
                "username": user["username"],
                "full_name": user["full_name"]
            }
        }
        
    except HTTPException as he:
        logger.warning(f"HTTPException during login: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error during user login: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )
