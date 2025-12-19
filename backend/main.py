from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import tempfile
import os
from typing import List, Dict, Any

from database import get_db, init_db
from document_service import DocumentService
from app.license_manager import get_license_verifier, LicenseExpiredError, LicenseInvalidError


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    yield


app = FastAPI(
    title="Nordicsecure RAG API",
    description="Private, offline RAG infrastructure for regulated industries",
    version="1.0.0",
    lifespan=lifespan
)

# Initialize document service
document_service = DocumentService()


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
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "License Expired. Contact support to renew.",
                    "error": str(e)
                }
            )
        except LicenseInvalidError as e:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "License Invalid. Contact support.",
                    "error": str(e)
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "License verification failed. Contact support.",
                    "error": str(e)
                }
            )
    
    return await call_next(request)


class SearchRequest(BaseModel):
    query: str


class IngestResponse(BaseModel):
    document_id: int
    filename: str
    message: str


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Nordicsecure RAG API is running"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Ingest a PDF document.
    
    This endpoint:
    1. Receives an uploaded PDF file
    2. Parses the text using PyPDF2 and/or OCR (Tesseract)
    3. Generates embeddings using Ollama
    4. Saves the document and embeddings to PostgreSQL
    
    Args:
        file: PDF file to ingest
        db: Database session
        
    Returns:
        Document ID and confirmation message
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Parse PDF to extract text
            text_content = document_service.parse_pdf(tmp_file_path)
            
            if not text_content.strip():
                raise HTTPException(
                    status_code=400, 
                    detail="No text content could be extracted from the PDF"
                )
            
            # Generate embedding for the document
            embedding = document_service.generate_embedding(text_content)
            
            # Save to database
            document_id = document_service.save_document(
                db=db,
                filename=file.filename,
                content=text_content,
                embedding=embedding
            )
            
            return IngestResponse(
                document_id=document_id,
                filename=file.filename,
                message="Document ingested successfully"
            )
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting document: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search for documents using semantic similarity.
    
    This endpoint:
    1. Receives a search query string
    2. Converts the query to an embedding using Ollama
    3. Searches PostgreSQL for matching documents using cosine similarity
    4. Returns the most relevant documents
    
    Args:
        request: Search request containing query string
        db: Database session
        
    Returns:
        List of matching documents with similarity scores
    """
    try:
        # Validate query
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Generate embedding for the query
        query_embedding = document_service.generate_embedding(request.query)
        
        # Search for similar documents
        results = document_service.search_documents(
            db=db,
            query_embedding=query_embedding,
            limit=5
        )
        
        return SearchResponse(results=results)
    
    except HTTPException:
        raise
    except Exception as e:
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
