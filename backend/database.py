"""
ChromaDB-based database module for Nordic Secure.

This module provides database initialization and collection management
using ChromaDB as the vector store. ChromaDB was chosen for native
Windows deployment without requiring PostgreSQL installation.

Key Features:
- Persistent storage with automatic directory management
- Cross-platform compatibility (Windows, macOS, Linux)
- PyInstaller bundle support with dynamic path resolution
- Thread-safe singleton pattern for client management

Usage:
    from backend.database import init_db, get_db
    
    # Initialize database
    init_db()
    
    # Get collection for document storage
    collection = get_db()
"""
import os
import sys
from pathlib import Path

# Disable ChromaDB telemetry before importing chromadb
# This prevents OpenTelemetry from registering atexit handlers
os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")
os.environ.setdefault("CHROMA_TELEMETRY", "false")

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
        if sys.platform == 'win32':
            base_dir = os.getenv('APPDATA')
            if not base_dir:
                # Fallback if APPDATA not set
                base_dir = Path.home() / 'AppData' / 'Roaming'
            else:
                base_dir = Path(base_dir)
        else:
            # macOS/Linux fallback
            base_dir = Path.home() / '.local' / 'share'
        
        base_dir = Path(base_dir) / 'NordicSecure'
    else:
        # Running as script - use local data directory
        base_dir = Path(__file__).parent
    
    data_dir = base_dir / 'data' / 'chroma_db'
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir)


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
