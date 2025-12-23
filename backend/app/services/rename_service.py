"""
RenameService - Intelligent PDF file renaming using LLM
Extracts Author and Title from PDF content and renames files accordingly
"""

import os
import re
import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class RenameService:
    """
    Service for intelligently renaming PDF files based on content.
    
    Features:
    - Extracts text from first 3 pages of PDF (not just filename)
    - Uses LLM to identify Author and Title
    - Renames files to "Author - Title.pdf" format
    - Handles UTF-8 characters (including Punjabi, Arabic, Chinese, etc.)
    - Safe renaming with collision detection
    - Supports multilingual content
    """
    
    # Maximum characters to send to LLM for analysis
    MAX_TEXT_LENGTH = 4000
    
    # Maximum filename length (to avoid filesystem limits)
    MAX_FILENAME_LENGTH = 200
    
    # Characters not allowed in filenames (Windows-safe)
    INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1f]'
    
    def __init__(
        self,
        document_service,
        ollama_base_url: str = "http://localhost:11435",
        model_name: str = "llama3"
    ):
        """
        Initialize RenameService.
        
        Args:
            document_service: DocumentService instance for PDF text extraction
            ollama_base_url: Base URL for Ollama API
            model_name: Name of LLM model to use for extraction
        """
        self.document_service = document_service
        self.ollama_base_url = ollama_base_url
        self.model_name = model_name
        self.rename_log: List[Dict[str, Any]] = []
    
    def extract_author_title(
        self,
        text: str,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Extract Author and Title from document text using LLM.
        
        Args:
            text: Extracted text from document (first 3 pages)
            max_retries: Number of retries if JSON parsing fails
            
        Returns:
            Dictionary with:
            - author: str (extracted author name)
            - title: str (extracted title)
            - confidence: float (optional)
            - success: bool
        """
        system_prompt = (
            "You are a bibliographic data extraction assistant. "
            "Your task is to analyze the beginning of a document (book, paper, or report) "
            "and extract the Author name and Title.\n\n"
            "IMPORTANT INSTRUCTIONS:\n"
            "1. Look at the CONTENT of the document, NOT the filename\n"
            "2. Extract the author's name (can be single author or multiple authors)\n"
            "3. Extract the full title of the document\n"
            "4. Handle multilingual content (English, Punjabi, Swedish, etc.)\n"
            "5. If multiple authors, format as 'FirstAuthor et al' or list all\n"
            "6. Preserve original language/script of author and title\n\n"
            "You MUST respond with valid JSON only. No additional text.\n\n"
            "Response format:\n"
            "{\n"
            '  "author": "Author Name(s)",\n'
            '  "title": "Document Title",\n'
            '  "confidence": 0.9\n'
            "}"
        )
        
        user_prompt = f"""Analyze this document excerpt and extract the Author and Title:

Document Text (first 3 pages):
{text[:self.MAX_TEXT_LENGTH]}

Extract the author and title in JSON format only."""
        
        for attempt in range(max_retries + 1):
            try:
                # Call Ollama API
                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": f"{system_prompt}\n\n{user_prompt}",
                        "stream": False,
                        "format": "json"
                    },
                    timeout=90  # Longer timeout for extraction task
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Extract response text
                response_text = result.get("response", "")
                
                # Parse JSON response
                try:
                    extraction = json.loads(response_text)
                    
                    # Validate response structure
                    if "author" in extraction and "title" in extraction:
                        author = str(extraction["author"]).strip()
                        title = str(extraction["title"]).strip()
                        
                        # Basic validation
                        if author and title and author.lower() not in ["unknown", "n/a", "none"]:
                            return {
                                "author": author,
                                "title": title,
                                "confidence": extraction.get("confidence", 0.8),
                                "success": True
                            }
                    
                    logger.warning(f"Invalid extraction: {extraction}")
                    if attempt < max_retries:
                        continue
                
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
                    
                    # Try to extract JSON from text
                    try:
                        start_idx = response_text.find('{')
                        if start_idx != -1:
                            depth = 0
                            for i in range(start_idx, len(response_text)):
                                if response_text[i] == '{':
                                    depth += 1
                                elif response_text[i] == '}':
                                    depth -= 1
                                    if depth == 0:
                                        json_str = response_text[start_idx:i+1]
                                        extraction = json.loads(json_str)
                                        if "author" in extraction and "title" in extraction:
                                            return {
                                                "author": str(extraction["author"]).strip(),
                                                "title": str(extraction["title"]).strip(),
                                                "confidence": extraction.get("confidence", 0.7),
                                                "success": True
                                            }
                                        break
                    except Exception as extract_error:
                        logger.debug(f"Could not extract JSON: {extract_error}")
                    
                    if attempt < max_retries:
                        continue
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Error calling Ollama API: {e}")
                if attempt < max_retries:
                    continue
                return {
                    "author": None,
                    "title": None,
                    "success": False,
                    "error": f"API error: {str(e)}"
                }
            except Exception as e:
                logger.error(f"Unexpected error during extraction: {e}")
                if attempt < max_retries:
                    continue
                return {
                    "author": None,
                    "title": None,
                    "success": False,
                    "error": f"Error: {str(e)}"
                }
        
        # Final fallback
        return {
            "author": None,
            "title": None,
            "success": False,
            "error": "Extraction failed after retries"
        }
    
    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string for use in a filename.
        
        - Removes invalid characters for Windows/Unix filesystems
        - Preserves UTF-8 characters (including Punjabi, Arabic, etc.)
        - Truncates to reasonable length
        - Handles edge cases
        
        Args:
            name: String to sanitize
            
        Returns:
            Sanitized filename-safe string
        """
        # Remove invalid characters but preserve UTF-8
        sanitized = re.sub(self.INVALID_CHARS, '', name)
        
        # Replace multiple spaces with single space
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Remove leading/trailing spaces and dots (Windows doesn't like trailing dots)
        sanitized = sanitized.strip(' .')
        
        # Truncate if too long (leave room for extension)
        if len(sanitized) > self.MAX_FILENAME_LENGTH:
            sanitized = sanitized[:self.MAX_FILENAME_LENGTH].strip()
        
        return sanitized
    
    def generate_new_filename(self, author: str, title: str) -> str:
        """
        Generate new filename in "Author - Title.pdf" format.
        
        Args:
            author: Author name
            title: Document title
            
        Returns:
            Sanitized filename with .pdf extension
        """
        # Sanitize components
        author_clean = self.sanitize_filename(author)
        title_clean = self.sanitize_filename(title)
        
        # Construct filename
        if author_clean and title_clean:
            new_name = f"{author_clean} - {title_clean}"
        elif title_clean:
            # Fallback: just title if no author
            new_name = title_clean
        elif author_clean:
            # Fallback: just author if no title
            new_name = author_clean
        else:
            # Ultimate fallback
            new_name = "Untitled"
        
        # Truncate if too long (reserve space for .pdf extension)
        if len(new_name) > self.MAX_FILENAME_LENGTH:
            new_name = new_name[:self.MAX_FILENAME_LENGTH].strip()
        
        # Add extension
        new_name = f"{new_name}.pdf"
        
        return new_name
    
    def safe_rename_file(
        self,
        source_path: Path,
        new_filename: str
    ) -> Tuple[Path, bool]:
        """
        Safely rename a file with collision handling.
        
        If target file exists, appends _1, _2, etc.
        
        Args:
            source_path: Path to source file
            new_filename: New filename (not full path)
            
        Returns:
            Tuple of (new_path, success)
        """
        target_path = source_path.parent / new_filename
        
        # Handle collision
        if target_path.exists() and target_path != source_path:
            stem = Path(new_filename).stem
            suffix = Path(new_filename).suffix
            counter = 1
            
            while target_path.exists():
                new_filename_numbered = f"{stem}_{counter}{suffix}"
                target_path = source_path.parent / new_filename_numbered
                counter += 1
                
                # Safety limit
                if counter > 1000:
                    logger.error(f"Too many files with similar names")
                    return (source_path, False)
        
        # Rename file with UTF-8 support
        try:
            # On Windows, Path.rename handles UTF-8 correctly
            source_path.rename(target_path)
            logger.info(f"Renamed: {source_path.name} -> {target_path.name}")
            return (target_path, True)
        except OSError as e:
            logger.error(f"Failed to rename {source_path.name}: {e}")
            return (source_path, False)
    
    def rename_single_file(
        self,
        file_path: Path,
        max_pages: int = 3
    ) -> Dict[str, Any]:
        """
        Rename a single PDF file based on its content.
        
        Args:
            file_path: Path to PDF file
            max_pages: Number of pages to extract for analysis (default: 3)
            
        Returns:
            Dictionary with:
            - original_name: str
            - new_name: str
            - success: bool
            - author: str
            - title: str
            - error: Optional[str]
        """
        original_name = file_path.name
        timestamp = datetime.now().isoformat()
        
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Extract text from first N pages
            parsed_data = self.document_service.parse_pdf(
                file_content,
                filename=original_name,
                max_pages=max_pages
            )
            
            # Get text from parsed pages
            pages = parsed_data.get("pages", [])
            text = "\n".join(page.get("text", "") for page in pages)
            
            if not text.strip():
                raise ValueError("No text could be extracted from document")
            
            # Extract author and title using LLM
            extraction = self.extract_author_title(text)
            
            if not extraction.get("success"):
                result = {
                    "original_name": original_name,
                    "new_name": original_name,
                    "success": False,
                    "author": None,
                    "title": None,
                    "error": extraction.get("error", "Extraction failed"),
                    "timestamp": timestamp
                }
                self.rename_log.append(result)
                return result
            
            # Generate new filename
            author = extraction["author"]
            title = extraction["title"]
            new_filename = self.generate_new_filename(author, title)
            
            # Rename file
            new_path, success = self.safe_rename_file(file_path, new_filename)
            
            result = {
                "original_name": original_name,
                "new_name": new_path.name,
                "success": success,
                "author": author,
                "title": title,
                "confidence": extraction.get("confidence"),
                "error": None if success else "Rename operation failed",
                "timestamp": timestamp
            }
            
            self.rename_log.append(result)
            return result
        
        except Exception as e:
            error_msg = f"Error processing {original_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            result = {
                "original_name": original_name,
                "new_name": original_name,
                "success": False,
                "author": None,
                "title": None,
                "error": str(e),
                "timestamp": timestamp
            }
            
            self.rename_log.append(result)
            return result
    
    def batch_rename(
        self,
        folder_path: str,
        max_pages: int = 3,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Batch rename all PDF files in a folder.
        
        Args:
            folder_path: Path to folder containing PDFs
            max_pages: Number of pages to analyze per file
            progress_callback: Optional callback function(current, total, result)
            
        Returns:
            Dictionary with:
            - total_files: int
            - processed: int
            - renamed: int
            - failed: int
            - rename_log: List[Dict]
        """
        folder = Path(folder_path)
        
        if not folder.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
        
        # Find all PDF files
        pdf_files = list(folder.glob("*.pdf")) + list(folder.glob("*.PDF"))
        total_files = len(pdf_files)
        
        logger.info(f"Found {total_files} PDF files to rename")
        
        # Reset rename log
        self.rename_log = []
        
        # Stats
        stats = {
            "total_files": total_files,
            "processed": 0,
            "renamed": 0,
            "failed": 0
        }
        
        # Process each file
        for i, file_path in enumerate(pdf_files, 1):
            result = self.rename_single_file(file_path, max_pages)
            
            # Update stats
            stats["processed"] += 1
            if result["success"]:
                stats["renamed"] += 1
            else:
                stats["failed"] += 1
            
            # Call progress callback
            if progress_callback:
                progress_callback(i, total_files, result)
        
        stats["rename_log"] = self.rename_log
        
        return stats
