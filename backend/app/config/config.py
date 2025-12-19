"""
Configuration module for NordicSecure backend.
Handles database connections, embedding models, and other settings.
"""

import os
from typing import Dict, Any


class Config:
    """Application configuration."""
    
    # Database configuration (PostgreSQL with pgvector)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "nordicsecure")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    # Embedding model configuration
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # Use local Ollama for embeddings (sovereign AI approach)
    USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "nomic-embed-text")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_db_config(cls) -> Dict[str, Any]:
        """Get database connection configuration."""
        return {
            "host": cls.DB_HOST,
            "port": cls.DB_PORT,
            "database": cls.DB_NAME,
            "user": cls.DB_USER,
            "password": cls.DB_PASSWORD
        }
    
    @classmethod
    def get_embedding_config(cls) -> Dict[str, Any]:
        """Get embedding model configuration."""
        return {
            "use_ollama": cls.USE_OLLAMA,
            "ollama_host": cls.OLLAMA_HOST,
            "ollama_model": cls.OLLAMA_MODEL,
            "embedding_model": cls.EMBEDDING_MODEL
        }
