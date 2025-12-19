"""
Example usage of DocumentService for PDF parsing and document storage.
This demonstrates the migrated functionality from the three legacy projects.
"""

import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import DocumentService
from app.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_pdf_parsing():
    """
    Example 1: Parse a PDF and extract text, tables, and invoice fields.
    
    This demonstrates the functionality migrated from:
    - pdf-api/extractionService.ts
    """
    print("\n" + "="*70)
    print("Example 1: PDF Parsing with Invoice Field Extraction")
    print("="*70 + "\n")
    
    # Initialize service (no database needed for parsing only)
    service = DocumentService()
    
    # Create a sample PDF in memory for demonstration
    # In real usage, you would read an actual PDF file:
    # with open("invoice.pdf", "rb") as f:
    #     pdf_bytes = f.read()
    
    # For this example, we'll use text-based demonstration
    sample_text = """
    INVOICE
    
    Invoice Number: INV-2024-001
    Invoice Date: 2024-12-19
    Due Date: 2025-01-19
    
    Supplier: NordicSecure AB
    Customer: Example Corporation
    
    Description          Quantity    Price      Total
    ------------------------------------------------
    Security Audit          1        5000.00    5000.00
    Compliance Review       1        3000.00    3000.00
    
    Subtotal:                                   8000.00
    VAT (25%):                                  2000.00
    Total Amount:                              10000.00 SEK
    
    Payment Terms: Net 30 days
    """
    
    print("Sample document text:")
    print("-" * 70)
    print(sample_text[:200] + "...\n")
    
    # Note: For actual PDF parsing, you would use:
    # result = service.parse_pdf(pdf_bytes, filename="invoice.pdf")
    
    print("In a real scenario, parse_pdf() would:")
    print("  ✓ Extract text from PDF using PyPDF2")
    print("  ✓ Detect if PDF is scanned and use OCR if needed")
    print("  ✓ Extract tables automatically")
    print("  ✓ Detect invoice fields with confidence scores:")
    print("    - Invoice number")
    print("    - Dates (invoice date, due date)")
    print("    - Amounts (total, subtotal, VAT)")
    print("    - Currency")
    print("    - Supplier and customer names")
    print("  ✓ Detect document language (Swedish/English)")
    
    print("\n" + "="*70 + "\n")


def example_document_storage():
    """
    Example 2: Store document with vector embeddings.
    
    This demonstrates the functionality migrated from:
    - Long-Term-Memory-API/worker.ts
    """
    print("\n" + "="*70)
    print("Example 2: Document Storage with Vector Embeddings")
    print("="*70 + "\n")
    
    # Check if database is configured
    db_config = Config.get_db_config()
    
    print("Database Configuration:")
    print(f"  Host: {db_config['host']}")
    print(f"  Port: {db_config['port']}")
    print(f"  Database: {db_config['database']}")
    print(f"  User: {db_config['user']}")
    print()
    
    # Initialize service with database config
    service = DocumentService(
        embedding_model="all-MiniLM-L6-v2",
        db_config=db_config
    )
    
    # Sample document text
    document_text = """
    NordicSecure Security Audit Report
    
    Executive Summary:
    This security audit was conducted for Example Corporation to assess
    their current security posture and compliance with GDPR requirements.
    The audit covered network security, data protection measures, and
    access control policies.
    
    Key Findings:
    - Strong encryption practices in place
    - Multi-factor authentication implemented
    - Regular security updates maintained
    - Room for improvement in incident response procedures
    """
    
    metadata = {
        "filename": "security_audit.pdf",
        "document_type": "audit_report",
        "client": "Example Corporation",
        "date": "2024-12-19",
        "category": "security"
    }
    
    print("Document to store:")
    print("-" * 70)
    print(document_text[:150] + "...\n")
    
    try:
        # Note: This will fail if database is not set up
        # result = service.store_document(
        #     text=document_text,
        #     metadata=metadata
        # )
        
        print("In a real scenario, store_document() would:")
        print("  ✓ Generate semantic embeddings using sentence-transformers")
        print("  ✓ Store document text and embeddings in PostgreSQL")
        print("  ✓ Use pgvector extension for efficient vector storage")
        print("  ✓ Store metadata as JSONB for flexible querying")
        print("  ✓ Return document ID and storage details")
        print("\nNote: Database must be configured and pgvector installed.")
        
    finally:
        service.close()
    
    print("\n" + "="*70 + "\n")


def example_complete_pipeline():
    """
    Example 3: Complete pipeline - Parse PDF and store with embeddings.
    """
    print("\n" + "="*70)
    print("Example 3: Complete Pipeline - Parse & Store")
    print("="*70 + "\n")
    
    print("Complete workflow:")
    print("  1. Parse PDF document")
    print("     - Extract text, tables, and invoice fields")
    print("     - Get confidence scores for extracted fields")
    print()
    print("  2. Generate vector embeddings")
    print("     - Use local sentence-transformers model")
    print("     - Or use Ollama for complete data sovereignty")
    print()
    print("  3. Store in PostgreSQL with pgvector")
    print("     - Document text and embeddings")
    print("     - Extracted metadata and fields")
    print()
    print("  4. Enable semantic search")
    print("     - Query documents by meaning, not just keywords")
    print("     - Find similar documents using vector similarity")
    
    print("\nCode example:")
    print("-" * 70)
    print("""
    # Complete pipeline
    service = DocumentService(db_config=Config.get_db_config())
    
    try:
        # Parse PDF
        with open("invoice.pdf", "rb") as f:
            parse_result = service.parse_pdf(f.read())
        
        # Store with embeddings
        storage_result = service.store_document(
            text=parse_result['raw_text'],
            metadata={
                "filename": "invoice.pdf",
                "invoice_number": parse_result['key_values']['invoice_number'],
                "total": parse_result['key_values']['total_amount']
            }
        )
        
        print(f"Stored as document ID: {storage_result['document_id']}")
    finally:
        service.close()
    """)
    
    print("\n" + "="*70 + "\n")


def example_data_sovereignty():
    """
    Example 4: Data Sovereignty - 100% local processing.
    """
    print("\n" + "="*70)
    print("Example 4: Data Sovereignty Features")
    print("="*70 + "\n")
    
    print("NordicSecure ensures complete data sovereignty:")
    print()
    print("✓ Local PDF Processing")
    print("  - PyPDF2 for text extraction")
    print("  - Tesseract OCR for scanned PDFs")
    print("  - All processing happens on your infrastructure")
    print()
    print("✓ Local Embedding Generation")
    print("  - sentence-transformers models run locally")
    print("  - Or use Ollama for complete offline operation")
    print("  - No data sent to OpenAI, Google, or cloud APIs")
    print()
    print("✓ Local Database Storage")
    print("  - PostgreSQL with pgvector extension")
    print("  - All data stays on your servers")
    print("  - Full control over data access and encryption")
    print()
    print("✓ Compliance Ready")
    print("  - GDPR compliant by design")
    print("  - Suitable for HIPAA, SOC 2, ISO 27001")
    print("  - No third-party data processors")
    print()
    print("Configuration for Ollama (optional):")
    print("-" * 70)
    print("""
    # In .env file:
    USE_OLLAMA=true
    OLLAMA_HOST=http://localhost:11434
    OLLAMA_MODEL=nomic-embed-text
    
    # Then embeddings will use local Ollama instance
    """)
    
    print("\n" + "="*70 + "\n")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("NordicSecure DocumentService Examples")
    print("="*70)
    print("\nDemonstrating migrated functionality from:")
    print("  - pdf-api: PDF parsing and invoice extraction")
    print("  - Long-Term-Memory-API: Vector embeddings and storage")
    print("  - AgentAudit: AI grounding and reliability")
    print("\n" + "="*70)
    
    # Run examples
    example_pdf_parsing()
    example_document_storage()
    example_complete_pipeline()
    example_data_sovereignty()
    
    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Install dependencies: pip install -r requirements.txt")
    print("  2. Set up PostgreSQL with pgvector extension")
    print("  3. Configure .env file with database credentials")
    print("  4. Try parsing real PDF files")
    print("  5. See backend/README.md for detailed usage")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
