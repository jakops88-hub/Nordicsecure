#!/usr/bin/env python3
# ==============================================================================
# IRON DOME: SECURITY & OFFLINE ENFORCEMENT
# Must be at the very top before ANY library imports to disable telemetry
# ==============================================================================
import os

# Disable LangChain telemetry and tracing
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_API_KEY"] = ""

# Disable SCARF analytics (used by some ML libraries)
os.environ["SCARF_NO_ANALYTICS"] = "true"

# Disable HuggingFace telemetry
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# ==============================================================================
# Robust Batch PDF Ingestion Pipeline
# ==============================================================================
"""
NordicSecure Batch PDF Ingestion Script

This script provides a robust, production-ready pipeline for ingesting multiple
PDF documents into the ChromaDB vector database.

Features:
- Corrupt file handling: Skips bad PDFs without crashing
- Size guardrail: Skips files larger than 50MB
- Memory management: Explicit garbage collection after every 10 files
- Error logging: Records all failures to failed_files.log
- Progress tracking: Real-time console updates

Usage:
    python backend/ingest.py <folder_path>
    
Example:
    python backend/ingest.py /path/to/legal/documents
"""

import sys
import gc
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services after environment setup
from backend.database import get_db, init_db
from backend.app.services.document_service import DocumentService

# Constants
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MEMORY_CLEANUP_INTERVAL = 10  # Run gc.collect() after every N files
FAILED_FILES_LOG = "failed_files.log"


def log_failed_file(filepath: str, error: str):
    """
    Log failed file to failed_files.log.
    
    Args:
        filepath: Path to the failed file
        error: Error message describing the failure
    """
    try:
        with open(FAILED_FILES_LOG, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {filepath} - {error}\n")
    except Exception as e:
        logger.error(f"Failed to write to {FAILED_FILES_LOG}: {e}")


def get_pdf_files(folder_path: Path) -> List[Path]:
    """
    Get all PDF files from a folder recursively.
    
    Args:
        folder_path: Path to the folder to scan
        
    Returns:
        List of Path objects for PDF files
    """
    pdf_files = []
    
    # Support various PDF extensions (case-insensitive)
    for pattern in ['*.pdf', '*.PDF', '*.Pdf']:
        pdf_files.extend(folder_path.rglob(pattern))
    
    # Remove duplicates and sort
    pdf_files = sorted(list(set(pdf_files)))
    
    return pdf_files


def check_file_size(filepath: Path) -> bool:
    """
    Check if file size is within acceptable limits.
    
    Args:
        filepath: Path to the file
        
    Returns:
        True if file size is acceptable, False otherwise
    """
    try:
        file_size = os.path.getsize(filepath)
        if file_size > MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            logger.warning(
                f"File too large for local beta: {filepath.name} "
                f"({size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB)"
            )
            log_failed_file(
                str(filepath),
                f"File too large: {size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB"
            )
            return False
        return True
    except Exception as e:
        logger.error(f"Error checking file size for {filepath}: {e}")
        log_failed_file(str(filepath), f"Error checking file size: {str(e)}")
        return False


def ingest_single_pdf(
    document_service: DocumentService,
    filepath: Path
) -> Dict[str, Any]:
    """
    Ingest a single PDF file with error handling.
    
    Args:
        document_service: DocumentService instance
        filepath: Path to the PDF file
        
    Returns:
        Dictionary with status and result information
    """
    try:
        # Check file size first
        if not check_file_size(filepath):
            return {
                "status": "skipped",
                "reason": "File too large",
                "filepath": str(filepath)
            }
        
        # Read file content
        with open(filepath, 'rb') as f:
            file_content = f.read()
        
        # Parse PDF with DocumentService
        logger.info(f"Processing: {filepath.name}")
        parsed_data = document_service.parse_pdf(
            file=file_content,
            filename=filepath.name
        )
        
        # Extract text content
        text_content = parsed_data.get("raw_text", "")
        
        if not text_content.strip():
            logger.warning(f"No text content extracted from: {filepath.name}")
            log_failed_file(
                str(filepath),
                "No text content could be extracted"
            )
            return {
                "status": "failed",
                "reason": "No text content",
                "filepath": str(filepath)
            }
        
        # Prepare metadata
        metadata = {
            "filename": filepath.name,
            "filepath": str(filepath),
            "pages_count": parsed_data.get("metadata", {}).get("pages_count", 0),
            "detected_language": parsed_data.get("metadata", {}).get("detected_language", "unknown"),
            "key_values": parsed_data.get("key_values", {}),
        }
        
        # Get pages information for precise source tracking
        pages = parsed_data.get("pages", [])
        
        # Store document with embeddings
        result = document_service.store_document(
            text=text_content,
            metadata=metadata,
            pages=pages
        )
        
        logger.info(
            f"✓ Successfully ingested: {filepath.name} "
            f"(ID: {result['document_id'][:8]}...)"
        )
        
        return {
            "status": "success",
            "document_id": result["document_id"],
            "filepath": str(filepath),
            "filename": filepath.name
        }
    
    except Exception as e:
        # Log the error but continue processing
        error_msg = str(e)
        logger.error(f"✗ Failed to ingest {filepath.name}: {error_msg}")
        log_failed_file(str(filepath), error_msg)
        
        return {
            "status": "failed",
            "reason": error_msg,
            "filepath": str(filepath),
            "filename": filepath.name
        }


def batch_ingest(folder_path: str) -> Dict[str, Any]:
    """
    Batch ingest all PDFs from a folder.
    
    Args:
        folder_path: Path to the folder containing PDF files
        
    Returns:
        Dictionary with statistics about the ingestion process
    """
    # Validate folder path
    folder = Path(folder_path)
    if not folder.exists():
        raise ValueError(f"Folder not found: {folder_path}")
    
    if not folder.is_dir():
        raise ValueError(f"Path is not a directory: {folder_path}")
    
    # Initialize database and service
    logger.info("Initializing ChromaDB...")
    init_db()
    collection = get_db()
    
    logger.info("Initializing DocumentService...")
    document_service = DocumentService(collection=collection)
    
    # Get all PDF files
    logger.info(f"Scanning folder: {folder_path}")
    pdf_files = get_pdf_files(folder)
    
    if not pdf_files:
        logger.warning(f"No PDF files found in: {folder_path}")
        return {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "results": []
        }
    
    logger.info(f"Found {len(pdf_files)} PDF files")
    logger.info(f"Failed files will be logged to: {FAILED_FILES_LOG}")
    logger.info("-" * 80)
    
    # Process each file
    stats = {
        "total_files": len(pdf_files),
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "results": []
    }
    
    for idx, pdf_file in enumerate(pdf_files, 1):
        logger.info(f"[{idx}/{len(pdf_files)}] Processing: {pdf_file.name}")
        
        # Ingest the file
        result = ingest_single_pdf(document_service, pdf_file)
        stats["results"].append(result)
        
        # Update statistics
        if result["status"] == "success":
            stats["successful"] += 1
        elif result["status"] == "failed":
            stats["failed"] += 1
        elif result["status"] == "skipped":
            stats["skipped"] += 1
        
        # Memory cleanup after every N files
        if idx % MEMORY_CLEANUP_INTERVAL == 0:
            logger.info(f"Running memory cleanup (processed {idx} files)...")
            gc.collect()
    
    # Final memory cleanup
    gc.collect()
    
    # Print summary
    logger.info("-" * 80)
    logger.info("Batch Ingestion Complete!")
    logger.info(f"Total files: {stats['total_files']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Skipped: {stats['skipped']}")
    
    if stats['failed'] > 0:
        logger.info(f"Check {FAILED_FILES_LOG} for details on failed files")
    
    return stats


def main():
    """
    Main entry point for the ingestion script.
    """
    if len(sys.argv) < 2:
        print("Usage: python backend/ingest.py <folder_path>")
        print("Example: python backend/ingest.py /path/to/legal/documents")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    try:
        stats = batch_ingest(folder_path)
        
        # Exit with error code if any files failed
        if stats['failed'] > 0:
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.warning("\nIngestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
