"""
DocumentService - Core service for PDF parsing and document storage
Migrated from:
- pdf-api: extractionService.ts (PDF parsing, OCR, table extraction)
- Long-Term-Memory-API: worker.ts (vector embeddings, storage)
"""

import io
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

try:
    import PyPDF2
    from pdf2image import convert_from_bytes
    import pytesseract
except ImportError:
    PyPDF2 = None
    convert_from_bytes = None
    pytesseract = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service for parsing PDFs and storing documents with vector embeddings.
    
    Features:
    - PDF text extraction with fallback to OCR for scanned PDFs
    - Table detection and extraction
    - Invoice field extraction (dates, amounts, parties)
    - Vector embedding generation for semantic search
    - Storage in PostgreSQL with pgvector extension
    """
    
    # Detection patterns (from pdf-api extractionService.ts)
    DATE_PATTERN = re.compile(
        r'\b(\d{4}[/.\-]\d{1,2}[/.\-]\d{1,2}|\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4})\b'
    )
    AMOUNT_PATTERN = re.compile(
        r'([+-]?\d{1,3}(?:[ .]\d{3})*(?:[.,]\d{2})|\d+[.,]\d{2})'
    )
    KNOWN_CURRENCIES = [
        "SEK", "USD", "EUR", "GBP", "NOK", "DKK", "CHF", "JPY",
        "kr", "dkk", "nok", "usd", "eur", "$", "€"
    ]
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        db_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize DocumentService.
        
        Args:
            embedding_model: Name of sentence-transformers model for embeddings
            db_config: PostgreSQL connection configuration
        """
        self.embedding_model_name = embedding_model
        self.embedding_model = None
        self.db_config = db_config or {}
        self.db_conn = None
        
        # Initialize embedding model lazily
        if SentenceTransformer is not None:
            try:
                self.embedding_model = SentenceTransformer(embedding_model)
                logger.info(f"Loaded embedding model: {embedding_model}")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
    
    def parse_pdf(self, file: bytes, filename: str = "document.pdf") -> Dict[str, Any]:
        """
        Parse a PDF file and extract text, tables, and metadata.
        
        Implements the extraction logic from pdf-api/extractionService.ts:
        - Attempts text extraction from PDF
        - Falls back to OCR if PDF appears to be scanned
        - Extracts tables from text
        - Detects invoice fields with confidence scores
        
        Args:
            file: PDF file as bytes
            filename: Name of the file
            
        Returns:
            Dictionary containing:
            - raw_text: Full extracted text
            - pages: List of page contents
            - tables: Detected tables
            - metadata: File metadata (name, page count, language)
            - key_values: Extracted invoice fields
            - key_values_confidence: Confidence scores for fields
        """
        if PyPDF2 is None:
            raise ImportError("PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2")
        
        logger.info(f"Starting PDF extraction for: {filename}")
        
        pages = []
        raw_text = ""
        page_count = 0
        
        try:
            # Step 1: Try text extraction from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file))
            page_count = len(pdf_reader.pages)
            
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text() or ""
                pages.append({
                    "page_number": i + 1,
                    "text": page_text
                })
                raw_text += page_text + "\n"
            
            # Step 2: Check if PDF is scanned (little to no text)
            if self._is_likely_scanned(raw_text):
                logger.info("PDF appears to be scanned. Falling back to OCR.")
                pages, raw_text = self._extract_with_ocr(file)
                page_count = len(pages)
        
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            raise
        
        # Step 3: Extract tables
        tables = self._extract_tables(pages)
        
        # Step 4: Extract key-value pairs (invoice fields)
        key_values, confidences, language = self._build_key_values(raw_text)
        
        result = {
            "raw_text": raw_text.strip(),
            "pages": pages,
            "tables": tables,
            "metadata": {
                "file_name": filename,
                "pages_count": page_count,
                "detected_language": language
            },
            "key_values": key_values,
            "key_values_confidence": confidences
        }
        
        logger.info(f"Successfully extracted {page_count} pages, {len(tables)} tables")
        return result
    
    def _is_likely_scanned(self, text: str) -> bool:
        """Check if PDF appears to be scanned (little meaningful text)."""
        if not text or len(text.strip()) < 100:
            return True
        # If less than 50% is alphabetic, likely scanned
        alpha_count = sum(c.isalpha() for c in text)
        return alpha_count < len(text) * 0.5
    
    def _extract_with_ocr(self, file: bytes) -> Tuple[List[Dict], str]:
        """
        Extract text from PDF using OCR (for scanned documents).
        
        Args:
            file: PDF file as bytes
            
        Returns:
            Tuple of (pages list, combined raw text)
        """
        if convert_from_bytes is None or pytesseract is None:
            raise ImportError(
                "OCR requires pdf2image and pytesseract. "
                "Install with: pip install pdf2image pytesseract"
            )
        
        pages = []
        try:
            images = convert_from_bytes(file)
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image)
                pages.append({
                    "page_number": i + 1,
                    "text": text
                })
            
            raw_text = "\n".join(p["text"] for p in pages)
            return pages, raw_text
        
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise
    
    def _extract_tables(self, pages: List[Dict]) -> List[Dict[str, Any]]:
        """
        Extract tables from page text.
        Looks for pipe-separated, tab-separated, or multi-space column patterns.
        """
        tables = []
        
        for page in pages:
            text = page.get("text", "")
            lines = text.split("\n")
            
            current_rows = []
            
            def flush_rows():
                if len(current_rows) >= 2:  # At least 2 rows to be a table
                    tables.append({
                        "page_number": page["page_number"],
                        "rows": current_rows.copy()
                    })
                current_rows.clear()
            
            for line in lines:
                if self._looks_like_table_row(line):
                    current_rows.append(self._split_row(line))
                else:
                    flush_rows()
            
            flush_rows()
        
        return tables
    
    def _looks_like_table_row(self, line: str) -> bool:
        """Check if a line looks like a table row."""
        if not line or not line.strip():
            return False
        
        trimmed = line.strip()
        has_pipes = "|" in trimmed
        has_tabs = "\t" in trimmed
        multi_space_columns = len(re.split(r'\s{2,}', trimmed)) >= 3
        
        return has_pipes or has_tabs or multi_space_columns
    
    def _split_row(self, line: str) -> List[str]:
        """Split a table row into columns."""
        if "|" in line:
            return [col.strip() for col in line.split("|") if col.strip()]
        
        if "\t" in line:
            return [col.strip() for col in line.split("\t") if col.strip()]
        
        # Multi-space separated
        return [col.strip() for col in re.split(r'\s{2,}', line.strip()) if col.strip()]
    
    def _build_key_values(self, text: str) -> Tuple[Dict, Dict, str]:
        """
        Extract invoice fields from text with confidence scores.
        
        Returns:
            Tuple of (key_values dict, confidence dict, detected language)
        """
        normalized_text = self._normalize_text(text)
        lines = self._split_into_lines(normalized_text)
        language = self._detect_language(normalized_text)
        
        # Extract various fields
        invoice_number = self._detect_invoice_number(lines, normalized_text)
        invoice_date = self._detect_date(
            lines, normalized_text,
            ["invoice date", "issue date", "fakturadatum", "datum"]
        )
        due_date = self._detect_date(
            lines, normalized_text,
            ["due date", "due", "förfallodatum", "forfallodatum"]
        )
        total_amount = self._detect_amount(
            lines,
            ["total", "totalt", "amount due", "total belopp"],
            prefer_highest=True
        )
        subtotal = self._detect_amount(
            lines,
            ["subtotal", "delsumma", "net total"],
            prefer_highest=False
        )
        vat = self._detect_amount(
            lines,
            ["vat", "moms", "tax"],
            prefer_highest=False
        )
        currency = self._detect_currency(lines, normalized_text)
        supplier = self._detect_party_name(
            lines,
            [re.compile(r'supplier', re.I), re.compile(r'leverantör', re.I)],
            fallback_index=0
        )
        customer = self._detect_party_name(
            lines,
            [re.compile(r'customer', re.I), re.compile(r'kund', re.I)],
            fallback_index=2
        )
        
        key_values = {
            "invoice_number": invoice_number["value"],
            "invoice_date": invoice_date["value"],
            "due_date": due_date["value"],
            "total_amount": total_amount["value"],
            "subtotal_amount": subtotal["value"],
            "vat_amount": vat["value"],
            "currency": currency["value"],
            "supplier_name": supplier["value"],
            "customer_name": customer["value"]
        }
        
        confidences = {
            "invoice_number": self._clamp_confidence(invoice_number["confidence"]),
            "invoice_date": self._clamp_confidence(invoice_date["confidence"]),
            "due_date": self._clamp_confidence(due_date["confidence"]),
            "total_amount": self._clamp_confidence(total_amount["confidence"]),
            "subtotal_amount": self._clamp_confidence(subtotal["confidence"]),
            "vat_amount": self._clamp_confidence(vat["confidence"]),
            "currency": self._clamp_confidence(currency["confidence"]),
            "supplier_name": self._clamp_confidence(supplier["confidence"]),
            "customer_name": self._clamp_confidence(customer["confidence"])
        }
        
        return key_values, confidences, language
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for processing."""
        return text.replace("\r\n", "\n").replace("\t", " ").strip()
    
    def _split_into_lines(self, text: str) -> List[str]:
        """Split text into non-empty lines."""
        return [line.strip() for line in text.split("\n") if line.strip()]
    
    def _detect_invoice_number(self, lines: List[str], full_text: str) -> Dict:
        """Detect invoice number from text."""
        keyword_patterns = [
            re.compile(r'invoice\s*(?:no|number|nr|#)\s*[:#-]?\s*([A-Za-z0-9-]{3,})', re.I),
            re.compile(r'inv\.\s*[:#-]?\s*([A-Za-z0-9-]{3,})', re.I),
            re.compile(r'faktura(?:nr|nummer)?\s*[:#-]?\s*([A-Za-z0-9-]{3,})', re.I)
        ]
        
        for line in lines:
            if "invoice date" in line.lower() or "fakturadatum" in line.lower():
                continue
            for pattern in keyword_patterns:
                match = pattern.search(line)
                if match:
                    return {"value": match.group(1), "confidence": 0.9}
        
        # Fallback
        fallback = re.search(r'\bINV[-\s]?[A-Z0-9]{3,}\b', full_text, re.I)
        if fallback:
            return {"value": fallback.group(0), "confidence": 0.5}
        
        return {"value": None, "confidence": 0}
    
    def _detect_date(
        self,
        lines: List[str],
        full_text: str,
        keywords: List[str]
    ) -> Dict:
        """Detect date near keywords."""
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords):
                match = self.DATE_PATTERN.search(line)
                if match:
                    return {"value": match.group(1), "confidence": 0.85}
        
        # Fallback: any date in text
        fallback = self.DATE_PATTERN.search(full_text)
        if fallback:
            return {"value": fallback.group(1), "confidence": 0.4}
        
        return {"value": None, "confidence": 0}
    
    def _detect_amount(
        self,
        lines: List[str],
        keywords: List[str],
        prefer_highest: bool = True
    ) -> Dict:
        """Detect monetary amount near keywords."""
        candidates = []
        
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords):
                match = self.AMOUNT_PATTERN.search(line)
                if match:
                    amount_str = match.group(1)
                    normalized = self._normalize_amount(amount_str)
                    numeric = self._amount_to_number(normalized)
                    candidates.append({
                        "value": normalized,
                        "confidence": 0.85,
                        "numeric": numeric
                    })
        
        if candidates:
            candidates.sort(
                key=lambda x: x["numeric"],
                reverse=prefer_highest
            )
            return {"value": candidates[0]["value"], "confidence": 0.85}
        
        # Fallback: any amount in text
        for line in lines:
            match = self.AMOUNT_PATTERN.search(line)
            if match:
                normalized = self._normalize_amount(match.group(1))
                return {"value": normalized, "confidence": 0.3}
        
        return {"value": None, "confidence": 0}
    
    def _normalize_amount(self, amount: str) -> str:
        """Normalize amount string."""
        # Remove spaces first
        amount = amount.replace(" ", "")
        # Replace comma with dot (but keep existing dots)
        # If there are multiple dots/commas, keep only the last one as decimal separator
        if "," in amount:
            # Replace comma with dot
            amount = amount.replace(",", ".")
        # Handle thousands separators: if multiple dots, remove all but last
        parts = amount.split(".")
        if len(parts) > 2:
            # Multiple dots - treat all but last as thousands separators
            amount = "".join(parts[:-1]) + "." + parts[-1]
        return amount
    
    def _amount_to_number(self, amount: str) -> float:
        """Convert amount string to number."""
        try:
            normalized = amount.replace(" ", "").replace(",", ".")
            return float(normalized)
        except (ValueError, AttributeError):
            return 0.0
    
    def _detect_currency(self, lines: List[str], full_text: str) -> Dict:
        """Detect currency code or symbol."""
        for line in lines:
            token = self._find_currency_token(line)
            if token:
                return {
                    "value": self._normalize_currency(token),
                    "confidence": 0.8
                }
        
        # Fallback
        token = self._find_currency_token(full_text)
        if token:
            return {
                "value": self._normalize_currency(token),
                "confidence": 0.5
            }
        
        return {"value": None, "confidence": 0}
    
    def _find_currency_token(self, text: str) -> Optional[str]:
        """Find currency token in text."""
        text_lower = text.lower()
        for currency in self.KNOWN_CURRENCIES:
            if currency.lower() in text_lower:
                return currency
        return None
    
    def _normalize_currency(self, token: str) -> str:
        """Normalize currency token."""
        upper = token.upper()
        if upper == "$":
            return "USD"
        if upper == "€":
            return "EUR"
        if upper == "KR":
            return "SEK"
        return upper
    
    def _detect_party_name(
        self,
        lines: List[str],
        patterns: List[re.Pattern],
        fallback_index: int = 0
    ) -> Dict:
        """Detect supplier or customer name."""
        for i, line in enumerate(lines):
            if any(pattern.search(line) for pattern in patterns):
                # Check if name is after colon
                parts = re.split(r'[:\-]', line)
                if len(parts) > 1 and parts[1].strip():
                    return {"value": parts[1].strip(), "confidence": 0.8}
                
                # Check next line
                if i + 1 < len(lines):
                    return {"value": lines[i + 1].strip(), "confidence": 0.7}
        
        # Fallback: use line at specific index
        if fallback_index < len(lines):
            return {"value": lines[fallback_index].strip(), "confidence": 0.3}
        
        return {"value": None, "confidence": 0}
    
    def _clamp_confidence(self, value: float) -> float:
        """Clamp confidence value between 0 and 1."""
        try:
            return max(0.0, min(1.0, round(value, 2)))
        except (ValueError, TypeError):
            return 0.0
    
    def _detect_language(self, text: str) -> str:
        """
        Detect language (Swedish or English) based on keywords.
        Simple heuristic-based detection.
        """
        text_lower = text.lower()
        
        swedish_keywords = [
            "faktura", "belopp", "förfallodatum", "org.nr",
            "kundnummer", "leverantör", "moms"
        ]
        english_keywords = [
            "invoice", "amount", "due date", "customer",
            "supplier", "tax", "subtotal"
        ]
        
        swedish_score = sum(1 for kw in swedish_keywords if kw in text_lower)
        english_score = sum(1 for kw in english_keywords if kw in text_lower)
        
        if swedish_score == 0 and english_score == 0:
            return "unknown"
        
        return "sv" if swedish_score >= english_score else "en"
    
    def store_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store document with vector embeddings in PostgreSQL.
        
        Implements storage logic from Long-Term-Memory-API/worker.ts:
        - Generates embedding from text using sentence-transformers
        - Stores in PostgreSQL with pgvector extension
        - Returns document ID and storage details
        
        Args:
            text: Document text to store
            metadata: Optional metadata (filename, user_id, etc.)
            
        Returns:
            Dictionary containing:
            - document_id: Generated document ID
            - embedding_dim: Dimension of embedding vector
            - stored_at: Timestamp
            - metadata: Stored metadata
        """
        if self.embedding_model is None:
            raise RuntimeError(
                "Embedding model not initialized. "
                "Install sentence-transformers: pip install sentence-transformers"
            )
        
        if psycopg2 is None:
            raise ImportError(
                "psycopg2 is required for database storage. "
                "Install with: pip install psycopg2-binary"
            )
        
        logger.info("Generating embedding for document")
        
        # Step 1: Generate embedding
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        embedding_list = embedding.tolist()
        
        logger.info(f"Generated {len(embedding_list)}-dimensional embedding")
        
        # Step 2: Prepare metadata
        metadata = metadata or {}
        metadata["stored_at"] = datetime.utcnow().isoformat()
        
        # Step 3: Store in database
        if not self.db_conn:
            self._connect_db()
        
        try:
            with self.db_conn.cursor() as cursor:
                # Create table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id SERIAL PRIMARY KEY,
                        text TEXT NOT NULL,
                        embedding vector(%s),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """, (len(embedding_list),))
                
                # Insert document
                cursor.execute("""
                    INSERT INTO documents (text, embedding, metadata, created_at)
                    VALUES (%s, %s::vector, %s::jsonb, NOW())
                    RETURNING id, created_at
                """, (
                    text,
                    f"[{','.join(map(str, embedding_list))}]",
                    psycopg2.extras.Json(metadata)
                ))
                
                doc_id, created_at = cursor.fetchone()
                self.db_conn.commit()
                
                logger.info(f"Stored document with ID: {doc_id}")
                
                return {
                    "document_id": doc_id,
                    "embedding_dim": len(embedding_list),
                    "stored_at": created_at.isoformat(),
                    "metadata": metadata
                }
        
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Failed to store document: {e}")
            raise
    
    def _connect_db(self):
        """Connect to PostgreSQL database."""
        if not self.db_config:
            raise ValueError("Database configuration not provided")
        
        self.db_conn = psycopg2.connect(**self.db_config)
        logger.info("Connected to PostgreSQL database")
    
    def close(self):
        """Close database connection."""
        if self.db_conn:
            self.db_conn.close()
            logger.info("Closed database connection")
