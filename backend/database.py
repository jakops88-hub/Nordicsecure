"""
ChromaDB-based database module for Nordic Secure.
Replaces PostgreSQL/pgvector with ChromaDB for native Windows deployment.
"""
import os
import sys
import chromadb
from chromadb.config import Settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_data_directory() -> str:
    """
    Get the data directory for ChromaDB storage.
    Uses relative path that works with PyInstaller.
    """
    # Check if running as PyInstaller bundle
    if getattr(sys, '_MEIPASS', None):
        # Running as executable - use user data directory
        base_dir = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'NordicSecure')
    else:
        # Running as script - use local data directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    data_dir = os.path.join(base_dir, 'data', 'chroma_db')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


# Global ChromaDB client instance
_chroma_client: Optional[chromadb.PersistentClient] = None


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Get or create the ChromaDB client instance.
    Uses persistent storage to save data across sessions.
    """
    global _chroma_client
    
    if _chroma_client is None:
        data_dir = get_data_directory()
        logger.info(f"Initializing ChromaDB with persistent storage at: {data_dir}")
        
        _chroma_client = chromadb.PersistentClient(
            path=data_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        logger.info("ChromaDB client initialized successfully")
    
    return _chroma_client


def get_or_create_collection(collection_name: str = "documents"):
    """
    Get or create a ChromaDB collection for storing documents.
    
    Args:
        collection_name: Name of the collection (default: "documents")
        
    Returns:
        ChromaDB collection instance
    """
    client = get_chroma_client()
    
    try:
        # Try to get existing collection
        collection = client.get_collection(name=collection_name)
        logger.info(f"Using existing collection: {collection_name}")
    except Exception:
        # Create new collection if it doesn't exist
        collection = client.create_collection(
            name=collection_name,
            metadata={"description": "Nordic Secure document storage"}
        )
        logger.info(f"Created new collection: {collection_name}")
    
    return collection


def get_db():
    """
    Compatibility function to maintain API similarity.
    Returns the ChromaDB collection.
    """
    return get_or_create_collection()


def init_db():
    """
    Initialize ChromaDB database.
    Creates the data directory and initializes the client.
    """
    try:
        client = get_chroma_client()
        collection = get_or_create_collection()
        logger.info(f"Database initialized. Collection count: {collection.count()}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
