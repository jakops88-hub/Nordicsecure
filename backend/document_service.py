import os
import tempfile
from typing import List, Dict, Any
import requests
from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from sqlalchemy.orm import Session
from database import Document


# Configuration constants
MIN_TEXT_LENGTH_FOR_DIGITAL_EXTRACTION = 100  # Minimum text length before falling back to OCR


class DocumentService:
    def __init__(self, ollama_url: str = None):
        self.ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://ollama:11434")
    
    def parse_pdf(self, pdf_path: str) -> str:
        """
        Parse PDF file, extracting text from both digital text and OCR for images.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        text_content = []
        
        try:
            # First, try to extract digital text using pypdf
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text.strip():
                    text_content.append(page_text)
            
            # If no text was extracted, or very little, use OCR
            if len(' '.join(text_content).strip()) < MIN_TEXT_LENGTH_FOR_DIGITAL_EXTRACTION:
                text_content = []
                # Convert PDF to images
                images = convert_from_path(pdf_path)
                
                # Apply OCR to each page
                for i, image in enumerate(images):
                    # Use Swedish language for OCR
                    ocr_text = pytesseract.image_to_string(image, lang='swe')
                    if ocr_text.strip():
                        text_content.append(ocr_text)
        
        except Exception as e:
            raise Exception(f"Error parsing PDF: {str(e)}")
        
        return '\n\n'.join(text_content)
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Ollama API.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": "nomic-embed-text",
                    "prompt": text
                }
            )
            response.raise_for_status()
            embedding = response.json()["embedding"]
            return embedding
        except Exception as e:
            raise Exception(f"Error generating embedding: {str(e)}")
    
    def save_document(self, db: Session, filename: str, content: str, embedding: List[float]) -> int:
        """
        Save document to database.
        
        Args:
            db: Database session
            filename: Name of the file
            content: Extracted text content
            embedding: Embedding vector
            
        Returns:
            Document ID
        """
        document = Document(
            filename=filename,
            content=content,
            embedding=embedding
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document.id
    
    def search_documents(self, db: Session, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents using cosine similarity.
        
        Args:
            db: Database session
            query_embedding: Query embedding vector
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents with similarity scores
        """
        # Use pgvector's cosine distance operator
        # Note: We use 1 - cosine_distance to get similarity score
        results = db.query(
            Document.id,
            Document.filename,
            Document.content,
            Document.embedding.cosine_distance(query_embedding).label("distance")
        ).order_by(
            Document.embedding.cosine_distance(query_embedding)
        ).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "filename": r.filename,
                "content": r.content,
                "similarity": 1 - r.distance  # Convert distance to similarity
            }
            for r in results
        ]
