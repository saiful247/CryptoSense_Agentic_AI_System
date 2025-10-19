from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import logging

# Import your authentication utilities
from app.auth.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Import your database operations
from app.db.firestore import (
    create_user,
    get_user_by_email,
    update_user,
    update_password
)

# Import your Pydantic schemas
from app.auth.schemas import UserCreate, UserResponse, Token, PasswordChange, UserLogin

# Create router
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# Logger for debugging
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user.

    - **email**: User's email address
    - **password**: User's password (will be hashed)
    """
    # Check if user already exists
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        # Hash the password
        password_hash = get_password_hash(user_data.password)

        # Prepare user data (excluding password from UserCreate)
        user_dict = user_data.dict(exclude={"password"})

        # Create user in database
        user_id = create_user(
            email=user_data.email,
            password_hash=password_hash,
            additional_data=user_dict  # Any additional fields from UserCreate
        )

        # Return user data (without sensitive info)
        return {
            "email": user_data.email,
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not register user"
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    This endpoint is for OAuth2 compatibility.

    - **username**: User's email address
    - **password**: User's password
    """
    # Get user by email (OAuth2 uses username field, but we use email)
    user = get_user_by_email(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user email as the subject
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "user_id": user["user_id"]}


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """
    Simple JSON login endpoint to get an access token.

    - **email**: User's email address
    - **password**: User's password
    """
    # Get user by email
    user = get_user_by_email(user_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Verify password
    if not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create access token with user email as the subject
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "user_id": user["user_id"]}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user information.
    """
    # Return user data from the dependency
    return {
        "email": current_user["email"],
        "user_id": current_user["user_id"]
    }


@router.get("/protected-resource")
async def get_protected_resource(current_user: dict = Depends(get_current_user)):
    """
    Example protected endpoint that requires authentication.
    """
    return {
        "message": f"Hello, {current_user['email']}! You have access to this protected resource."
    }


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """
    Change user password. Requires authentication.

    - **current_password**: User's current password
    - **new_password**: User's new password
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    try:
        # Hash the new password
        new_password_hash = get_password_hash(password_data.new_password)

        # Update the password in the database
        success = update_password(current_user["user_id"], new_password_hash)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )

        return {"message": "Password updated successfully"}

    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not change password"
        )
