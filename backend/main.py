from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import tempfile
import os
import logging
from typing import List, Dict, Any

from database import get_db, init_db
from app.services.document_service import DocumentService
from app.license_manager import get_license_verifier, LicenseExpiredError, LicenseInvalidError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global document service instance
document_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and document service on startup"""
    global document_service
    
    # Initialize ChromaDB
    init_db()
    
    # Get ChromaDB collection
    collection = get_db()
    
    # Initialize document service with collection
    document_service = DocumentService(collection=collection)
    logger.info("Document service initialized with ChromaDB")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down application")


app = FastAPI(
    title="Nordicsecure RAG API",
    description="Private, offline RAG infrastructure for regulated industries",
    version="1.0.0",
    lifespan=lifespan
)


# License verification middleware
@app.middleware("http")
async def license_check_middleware(request: Request, call_next):
    """
    Middleware to check license before processing protected endpoints.
    
    Protected endpoints: /search, /ingest
    Unprotected endpoints: /, /health
    """
    path = request.url.path
    
    # Allow health check and root endpoint without license
    if path in ["/", "/health"]:
        return await call_next(request)
    
    # Check license for protected endpoints
    if path in ["/search", "/ingest"]:
        try:
            verifier = get_license_verifier()
            verifier.check_license()
        except LicenseExpiredError as e:
            # Log full error details server-side
            logger.warning(f"License expired: {str(e)}")
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "License Expired. Contact support to renew."
                }
            )
        except LicenseInvalidError as e:
            # Log full error details server-side
            logger.warning(f"Invalid license: {str(e)}")
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "License Invalid. Contact support."
                }
            )
        except Exception as e:
            # Log full error details server-side
            logger.error(f"License verification error: {str(e)}")
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "License verification failed. Contact support."
                }
            )
    
    return await call_next(request)


class SearchRequest(BaseModel):
    query: str


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    message: str


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Nordicsecure RAG API is running"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)):
    """
    Ingest a PDF document.
    
    This endpoint:
    1. Receives an uploaded PDF file
    2. Parses the text and metadata using PyPDF2 and/or OCR (Tesseract)
    3. Generates embeddings using sentence-transformers
    4. Saves the document and embeddings to ChromaDB
    
    Args:
        file: PDF file to ingest
        
    Returns:
        Document ID and confirmation message
    """
    global document_service
    
    if document_service is None:
        raise HTTPException(status_code=500, detail="Document service not initialized")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse PDF to extract text and metadata
        parsed_data = document_service.parse_pdf(content, filename=file.filename)
        
        # Extract raw text
        text_content = parsed_data.get("raw_text", "")
        
        if not text_content.strip():
            raise HTTPException(
                status_code=400, 
                detail="No text content could be extracted from the PDF"
            )
        
        # Prepare metadata
        metadata = {
            "filename": file.filename,
            "pages_count": parsed_data.get("metadata", {}).get("pages_count", 0),
            "detected_language": parsed_data.get("metadata", {}).get("detected_language", "unknown"),
            "key_values": parsed_data.get("key_values", {}),
        }
        
        # Get pages information for precise source tracking
        pages = parsed_data.get("pages", [])
        
        # Store document with embeddings, using page-level chunking
        result = document_service.store_document(
            text=text_content,
            metadata=metadata,
            pages=pages
        )
        
        return IngestResponse(
            document_id=result["document_id"],
            filename=file.filename,
            message="Document ingested successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error ingesting document: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Search for documents using semantic similarity.
    
    This endpoint:
    1. Receives a search query string
    2. Converts the query to an embedding using sentence-transformers
    3. Searches ChromaDB for matching documents using cosine similarity
    4. Returns the most relevant documents
    
    Args:
        request: Search request containing query string
        
    Returns:
        List of matching documents with similarity scores
    """
    global document_service
    
    if document_service is None:
        raise HTTPException(status_code=500, detail="Document service not initialized")
    
    try:
        # Validate query
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Search for similar documents
        results = document_service.search_documents(
            query_text=request.query,
            limit=5
        )
        
        return SearchResponse(results=results)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")


@app.get("/health")
async def health_check():
    """Extended health check endpoint"""
    return {
        "status": "healthy",
        "service": "Nordicsecure RAG API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Default configuration
    host = "0.0.0.0"
    port = 8000
    
    # Parse command line arguments
    for i, arg in enumerate(sys.argv):
        if arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
    
    # Run the application
    uvicorn.run(app, host=host, port=port)
