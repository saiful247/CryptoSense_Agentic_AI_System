# app/db/nft_firestore.py
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from google.cloud import firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

project_id = os.getenv("FIRESTORE_PROJECT_ID")
db_name = os.getenv("FIRESTORE_DATABASE_NAME", "irwa-crypto-agent-user")

# Initialize Firestore client
db = firestore.Client(project=project_id, database=db_name)

# NFT Collection Reference
nft_collection = db.collection("nft_data")


def create_nft_data(user_id: str, nft_data: Dict[str, Any]) -> str:
    """
    Create a new NFT record in Firestore under the nft_data collection.

    Args:
        user_id: ID of the user creating the NFT
        nft_data: The NFTResponse data (dict form)

    Returns:
        str: Document ID of the created NFT record
    """
    data = {
        "user_id": user_id,
        "nft_data": nft_data,
        "created_at": datetime.utcnow()
    }

    doc_ref = nft_collection.document()
    doc_ref.set(data)
    return doc_ref.id


def get_nft_data_by_user(user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all NFT data created by a specific user.

    Args:
        user_id: User's ID

    Returns:
        List: A list of NFT records
    """
    query = nft_collection.where("user_id", "==", user_id)
    results = query.stream()

    nft_list = []
    for doc in results:
        nft_entry = doc.to_dict()
        nft_entry["nft_id"] = doc.id
        nft_list.append(nft_entry)

    return nft_list


def delete_nft_data(nft_id: str) -> bool:
    """
    Delete an NFT record by its document ID.

    Args:
        nft_id: Firestore document ID of the NFT record

    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        nft_collection.document(nft_id).delete()
        return True
    except Exception as e:
        print(f"Error deleting NFT data: {e}")
        return False
