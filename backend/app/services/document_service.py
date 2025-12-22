"""
DocumentService - Core service for PDF parsing and document storage
Migrated from:
- pdf-api: extractionService.ts (PDF parsing, OCR, table extraction)
- Long-Term-Memory-API: worker.ts (vector embeddings, storage)

Updated to use ChromaDB for native Windows deployment.
"""

import io
import re
import os
import sys
import hashlib
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
    import chromadb
except ImportError:
    chromadb = None

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
    
    # Placeholder text for empty pages (maintains consistent page numbering)
    EMPTY_PAGE_PLACEHOLDER = "[Empty page {}]"
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        collection=None
    ):
        """
        Initialize DocumentService.
        
        Args:
            embedding_model: Name of sentence-transformers model for embeddings
            collection: ChromaDB collection instance (optional)
        """
        self.embedding_model_name = embedding_model
        self.embedding_model = None
        self.collection = collection
        
        # Set portable Tesseract path for PyInstaller
        self._configure_tesseract_path()
        
        # Initialize embedding model lazily
        if SentenceTransformer is not None:
            try:
                self.embedding_model = SentenceTransformer(embedding_model)
                logger.info(f"Loaded embedding model: {embedding_model}")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
    
    def _configure_tesseract_path(self):
        """
        Configure Tesseract OCR path for portable deployment.
        Points to ./bin/tesseract/tesseract.exe for PyInstaller bundles.
        """
        if pytesseract is None:
            return
        
        # Check if running as PyInstaller bundle
        if getattr(sys, '_MEIPASS', None):
            # Running as executable
            base_dir = sys._MEIPASS
        else:
            # Running as script - go up to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        tesseract_path = os.path.join(base_dir, 'bin', 'tesseract', 'tesseract.exe')
        
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.info(f"Using portable Tesseract at: {tesseract_path}")
        else:
            logger.warning(f"Tesseract not found at: {tesseract_path}. Will use system default.")
    
    def parse_pdf(self, file: bytes, filename: str = "document.pdf", max_pages: Optional[int] = None) -> Dict[str, Any]:
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
            max_pages: Optional limit on number of pages to extract (for lazy loading)
            
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
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                logger.warning(f"PDF {filename} is encrypted")
                raise ValueError("Cannot process encrypted PDF files. Please provide an unencrypted version.")
            
            page_count = len(pdf_reader.pages)
            
            # Handle empty PDFs
            if page_count == 0:
                logger.warning(f"PDF {filename} has no pages")
                raise ValueError("PDF file is empty (0 pages)")
            
            # Limit pages if max_pages is specified
            pages_to_extract = page_count if max_pages is None else min(max_pages, page_count)
            
            for i, page in enumerate(pdf_reader.pages[:pages_to_extract]):
                try:
                    page_text = page.extract_text() or ""
                except Exception as page_error:
                    logger.warning(f"Error extracting text from page {i + 1}: {page_error}")
                    page_text = ""
                
                pages.append({
                    "page_number": i + 1,
                    "text": page_text
                })
                raw_text += page_text + "\n"
            
            # Step 2: Check if PDF is scanned (little to no text)
            if self._is_likely_scanned(raw_text):
                logger.info("PDF appears to be scanned. Falling back to OCR.")
                try:
                    pages, raw_text = self._extract_with_ocr(file, max_pages=max_pages)
                    page_count = len(pages)
                except ImportError as ocr_error:
                    logger.error(f"OCR not available: {ocr_error}")
                    raise ValueError(
                        "PDF appears to be scanned but OCR is not available. "
                        "Install pdf2image and pytesseract."
                    ) from ocr_error
                except Exception as ocr_error:
                    logger.error(f"OCR failed: {ocr_error}")
                    raise ValueError(
                        f"Failed to extract text via OCR: {str(ocr_error)}"
                    ) from ocr_error
        
        except ValueError:
            # Re-raise ValueError exceptions (encrypted, empty, OCR issues)
            raise
        except Exception as e:
            logger.error(f"Error extracting PDF {filename}: {e}", exc_info=True)
            raise ValueError(f"Failed to parse PDF: {str(e)}") from e
        
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
    
    def _extract_with_ocr(self, file: bytes, max_pages: Optional[int] = None) -> Tuple[List[Dict], str]:
        """
        Extract text from PDF using OCR (for scanned documents).
        
        Args:
            file: PDF file as bytes
            max_pages: Optional limit on number of pages to extract
            
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
            
            # Limit pages if max_pages is specified
            images_to_process = images if max_pages is None else images[:max_pages]
            
            for i, image in enumerate(images_to_process):
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
                """Add accumulated rows to tables list if enough rows exist."""
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
        metadata: Optional[Dict[str, Any]] = None,
        pages: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Store document with vector embeddings in ChromaDB.
        
        Implements storage logic using ChromaDB instead of PostgreSQL:
        - Generates embedding from text using sentence-transformers
        - Stores in ChromaDB with metadata
        - Returns document ID and storage details
        
        If pages are provided, stores each page as a separate chunk for precise
        source citation (page and line numbers).
        
        Args:
            text: Document text to store (used if pages not provided)
            metadata: Optional metadata (filename, user_id, etc.)
            pages: Optional list of pages with structure [{"page_number": int, "text": str}]
            
        Returns:
            Dictionary containing:
            - document_id: Generated document ID (or base ID if pages provided)
            - chunks_stored: Number of chunks stored
            - embedding_dim: Dimension of embedding vector
            - stored_at: Timestamp
            - metadata: Stored metadata
        """
        if self.embedding_model is None:
            raise RuntimeError(
                "Embedding model not initialized. "
                "Install sentence-transformers: pip install sentence-transformers"
            )
        
        if chromadb is None:
            raise ImportError(
                "chromadb is required for database storage. "
                "Install with: pip install chromadb"
            )
        
        if self.collection is None:
            raise RuntimeError(
                "ChromaDB collection not initialized. "
                "Pass collection instance to DocumentService constructor."
            )
        
        stored_at = datetime.utcnow().isoformat()
        base_metadata = metadata or {}
        base_metadata["stored_at"] = stored_at
        
        # Generate base document ID
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        
        # If pages provided, store each page as a separate chunk
        if pages and len(pages) > 0:
            logger.info(f"Storing document with {len(pages)} page chunks")
            
            embeddings_list = []
            documents_list = []
            metadatas_list = []
            ids_list = []
            
            for page in pages:
                page_num = page.get("page_number", 0)
                page_text = page.get("text", "")
                
                # Store even empty pages to maintain consistent page numbering
                # Use placeholder text for empty pages
                if not page_text.strip():
                    page_text = self.EMPTY_PAGE_PLACEHOLDER.format(page_num)
                    logger.debug(f"Page {page_num} is empty, using placeholder")
                
                # Generate embedding for this page
                embedding = self.embedding_model.encode(page_text, convert_to_numpy=True)
                embeddings_list.append(embedding.tolist())
                documents_list.append(page_text)
                
                # Create page-specific metadata
                page_metadata = base_metadata.copy()
                page_metadata["page_number"] = page_num
                page_metadata["total_pages"] = len(pages)
                metadatas_list.append(page_metadata)
                
                # Create page-specific ID
                page_hash = hashlib.md5(page_text.encode()).hexdigest()[:8]
                page_id = f"doc_{timestamp}_page{page_num}_{page_hash}"
                ids_list.append(page_id)
            
            if not embeddings_list:
                raise ValueError("No valid pages with text content found")
            
            # Store all pages in ChromaDB with error handling
            try:
                self.collection.add(
                    embeddings=embeddings_list,
                    documents=documents_list,
                    metadatas=metadatas_list,
                    ids=ids_list
                )
                
                logger.info(f"Stored {len(embeddings_list)} page chunks")
                
                return {
                    "document_id": f"doc_{timestamp}",
                    "chunks_stored": len(embeddings_list),
                    "embedding_dim": len(embeddings_list[0]) if embeddings_list else 0,
                    "stored_at": stored_at,
                    "metadata": base_metadata
                }
            
            except Exception as e:
                logger.error(f"Failed to store document pages in ChromaDB: {e}", exc_info=True)
                raise RuntimeError(f"ChromaDB storage failed: {str(e)}") from e
        
        else:
            # Legacy behavior: store entire document as single chunk
            logger.info("Storing document as single chunk")
            
            # Step 1: Generate embedding
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            embedding_list = embedding.tolist()
            
            logger.info(f"Generated {len(embedding_list)}-dimensional embedding")
            
            # Step 2: Generate document ID
            doc_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            doc_id = f"doc_{timestamp}_{doc_hash}"
            
            # Step 3: Store in ChromaDB with error handling
            try:
                self.collection.add(
                    embeddings=[embedding_list],
                    documents=[text],
                    metadatas=[base_metadata],
                    ids=[doc_id]
                )
                
                logger.info(f"Stored document with ID: {doc_id}")
                
                return {
                    "document_id": doc_id,
                    "chunks_stored": 1,
                    "embedding_dim": len(embedding_list),
                    "stored_at": stored_at,
                    "metadata": base_metadata
                }
            
            except Exception as e:
                logger.error(f"Failed to store document in ChromaDB: {e}", exc_info=True)
                raise RuntimeError(f"ChromaDB storage failed: {str(e)}") from e
    
    def _find_best_matching_line(
        self,
        text: str,
        query_text: str
    ) -> Tuple[int, str]:
        """
        Find the best matching line in text for a query.
        
        Args:
            text: The document text to search in
            query_text: The query text to search for
            
        Returns:
            Tuple of (line_number, matched_line_text)
            Returns (1, first_line) if no good match found
        """
        lines = text.split('\n')
        if not lines:
            return (1, "")
        
        # Normalize query once for better performance
        query_lower = query_text.lower()
        query_words = set(query_lower.split())
        
        # Pre-compute lowercased lines for efficiency
        lines_lower = [line.lower() for line in lines]
        
        best_line_num = 1
        best_score = 0
        best_line_text = lines[0] if lines else ""
        
        for i, (line, line_lower) in enumerate(zip(lines, lines_lower), start=1):
            if not line.strip():
                continue
            
            # Check for exact phrase match first (most important)
            if query_lower in line_lower:
                return (i, line.strip())
            
            # Calculate word overlap score
            line_words = set(line_lower.split())
            overlap = len(query_words & line_words)
            
            if overlap > best_score:
                best_score = overlap
                best_line_num = i
                best_line_text = line.strip()
        
        # Return best match found, or first non-empty line
        if best_score > 0:
            return (best_line_num, best_line_text)
        
        # Fallback: return first non-empty line
        for i, line in enumerate(lines, start=1):
            if line.strip():
                return (i, line.strip())
        
        return (1, best_line_text)
    
    def search_documents(
        self,
        query_text: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query_text: Query text to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents with similarity scores and source citations
            Each result includes:
            - id: Document/chunk ID
            - document: Full text of the matching chunk
            - metadata: Document metadata including filename
            - distance: Similarity distance (lower is better)
            - page: Page number where match was found (if available)
            - row: Line/row number within the page (if available)
        """
        if self.embedding_model is None:
            raise RuntimeError("Embedding model not initialized")
        
        if self.collection is None:
            raise RuntimeError("ChromaDB collection not initialized")
        
        logger.info(f"Searching for: {query_text}")
        
        # Generate query embedding with error handling
        try:
            query_embedding = self.embedding_model.encode(query_text, convert_to_numpy=True)
            query_embedding_list = query_embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}", exc_info=True)
            raise RuntimeError(f"Embedding generation failed: {str(e)}") from e
        
        # Search in ChromaDB with error handling
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding_list],
                n_results=limit
            )
            
            # Format results with source citations
            formatted_results = []
            if results and results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    doc_text = results['documents'][0][i]
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    
                    # Extract page number from metadata
                    page_number = metadata.get('page_number')
                    
                    # Find best matching line in the document
                    line_number, matched_line = self._find_best_matching_line(doc_text, query_text)
                    
                    result = {
                        "id": results['ids'][0][i] if results['ids'] else None,
                        "document": doc_text,
                        "metadata": metadata,
                        "distance": results['distances'][0][i] if results['distances'] else None,
                    }
                    
                    # Add source citation information
                    if page_number is not None:
                        result["page"] = page_number
                    
                    result["row"] = line_number
                    result["matched_line"] = matched_line
                    
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} matching documents with source citations")
            return formatted_results
        
        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}", exc_info=True)
            raise RuntimeError(f"Search operation failed: {str(e)}") from e
