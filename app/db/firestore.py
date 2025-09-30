import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from google.cloud import firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set credentials and project ID from environment variables
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS")
project_id = os.getenv("FIRESTORE_PROJECT_ID")
db_name = os.getenv("FIRESTORE_DATABASE_NAME", "irwa-crypto-agent-user")

# Initialize Firestore client
db = firestore.Client(project=project_id, database=db_name)

# User Collection Reference
user_collection = db.collection("users")


def create_user(email: str, password_hash: str, additional_data: dict = None) -> str:
    """
    Create a new user in Firestore.

    Args:
        email: User's email address
        password_hash: Hashed password (NEVER store plain passwords)
        additional_data: Any additional user information

    Returns:
        str: User ID of the created user
    """
    # Create user data dictionary
    user_data = {
        "email": email,
        "password_hash": password_hash,
        "created_at": datetime.utcnow()
    }

    # Add additional data if provided
    if additional_data:
        user_data.update(additional_data)

    # Check if user with this email already exists
    existing_user = get_user_by_email(email)
    if existing_user:
        raise ValueError(f"User with email {email} already exists")

    # Create new user document with auto-generated ID
    doc_ref = user_collection.document()
    doc_ref.set(user_data)

    # Return the document ID as user_id
    return doc_ref.id


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user by email address.

    Args:
        email: User's email address

    Returns:
        Dict or None: User data if found, None otherwise
    """
    # Query Firestore for user with matching email
    query = user_collection.where("email", "==", email).limit(1)
    results = query.stream()

    # Get the first (and should be only) result
    for doc in results:
        user_data = doc.to_dict()
        user_data["user_id"] = doc.id  # Add document ID as user_id
        return user_data

    # No user found
    return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user by ID.

    Args:
        user_id: User's ID (Firestore document ID)

    Returns:
        Dict or None: User data if found, None otherwise
    """
    # Get document reference and retrieve
    doc_ref = user_collection.document(user_id)
    doc = doc_ref.get()

    # Check if document exists
    if doc.exists:
        user_data = doc.to_dict()
        user_data["user_id"] = doc.id  # Add document ID as user_id
        return user_data

    # No user found
    return None


def update_user(user_id: str, update_data: Dict[str, Any]) -> bool:
    """
    Update user information.

    Args:
        user_id: User's ID (Firestore document ID)
        update_data: Dictionary of fields to update

    Returns:
        bool: True if successful, False otherwise
    """
    # Remove sensitive fields if present
    if "password_hash" in update_data:
        # Password should be updated through a dedicated function
        del update_data["password_hash"]

    # Add update timestamp
    update_data["updated_at"] = datetime.utcnow()

    try:
        # Update the document
        user_collection.document(user_id).update(update_data)
        return True
    except Exception as e:
        print(f"Error updating user: {e}")
        return False


def update_password(user_id: str, new_password_hash: str) -> bool:
    """
    Update a user's password hash.

    Args:
        user_id: User's ID (Firestore document ID)
        new_password_hash: New hashed password

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Update only the password_hash field
        user_collection.document(user_id).update({
            "password_hash": new_password_hash,
            "password_updated_at": datetime.utcnow()
        })
        return True
    except Exception as e:
        print(f"Error updating password: {e}")
        return False


def delete_user(user_id: str) -> bool:
    """
    Delete a user from Firestore.

    Args:
        user_id: User's ID (Firestore document ID)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        user_collection.document(user_id).delete()
        return True
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False


def list_users(limit: int = 100) -> List[Dict[str, Any]]:
    """
    List all users (with pagination).

    Args:
        limit: Maximum number of users to return

    Returns:
        List: List of user data dictionaries
    """
    users = []
    query = user_collection.limit(limit)

    for doc in query.stream():
        user_data = doc.to_dict()
        user_data["user_id"] = doc.id  # Add document ID as user_id

        # Remove sensitive information
        if "password_hash" in user_data:
            del user_data["password_hash"]

        users.append(user_data)

    return users
