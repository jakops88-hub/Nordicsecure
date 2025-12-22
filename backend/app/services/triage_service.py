"""
Triage Service - Batch file sorting with AI classification
Analyzes files against user criteria and sorts them into folders
"""

import os
import re
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import pandas as pd
import requests

logger = logging.getLogger(__name__)


class TriageService:
    """
    Service for batch sorting files using AI classification.
    
    Features:
    - Lazy loading: Only reads first N pages of PDFs to save time
    - LLM prompting: Uses Ollama (Llama 3) for classification with JSON response
    - File handling: Safe move operations with collision detection
    - Error handling: Continues processing if individual files fail
    - Audit trail: Logs all decisions for compliance
    """
    
    # Maximum characters to send to LLM for classification (to avoid token limits)
    MAX_TEXT_LENGTH = 3000
    
    # Supported file patterns (case variations)
    PDF_PATTERNS = ['*.pdf', '*.PDF', '*.Pdf']
    
    def __init__(
        self,
        document_service,
        ollama_base_url: str = "http://localhost:11435",
        model_name: str = "llama3"
    ):
        """
        Initialize TriageService.
        
        Args:
            document_service: DocumentService instance for OCR and text extraction
            ollama_base_url: Base URL for Ollama API
            model_name: Name of LLM model to use for classification
        """
        self.document_service = document_service
        self.ollama_base_url = ollama_base_url
        self.model_name = model_name
        self.audit_log: List[Dict[str, Any]] = []
    
    def classify_document(
        self,
        text: str,
        criteria: str,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Classify a document using LLM based on user criteria.
        
        Args:
            text: Extracted text from document
            criteria: User-defined sorting criteria
            max_retries: Number of retries if JSON parsing fails
            
        Returns:
            Dictionary with:
            - is_relevant: bool
            - reason: str (explanation from AI)
            - confidence: float (optional)
        """
        system_prompt = """You are a document classification assistant. Your task is to analyze documents and determine if they match the given criteria.

IMPORTANT: You MUST respond with valid JSON only. No additional text before or after the JSON.

Response format:
{
  "is_relevant": true/false,
  "reason": "Brief explanation of why the document is or isn't relevant"
}"""
        
        user_prompt = f"""Classification Criteria: {criteria}

Document Text (excerpt):
{text[:self.MAX_TEXT_LENGTH]}

Does this document match the criteria? Respond in JSON format only."""
        
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
                    timeout=60
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Extract response text
                response_text = result.get("response", "")
                
                # Parse JSON response with robust extraction
                try:
                    # Try direct JSON parsing first
                    classification = json.loads(response_text)
                    
                    # Validate response structure
                    if "is_relevant" in classification and "reason" in classification:
                        return {
                            "is_relevant": bool(classification["is_relevant"]),
                            "reason": str(classification["reason"])
                        }
                    else:
                        logger.warning(f"Invalid response structure: {classification}")
                        if attempt < max_retries:
                            continue
                
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
                    
                    # Try to extract JSON from text that may have extra content
                    # Look for JSON object between { and }
                    try:
                        json_match = re.search(r'\{[^{}]*"is_relevant"[^{}]*\}', response_text, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            classification = json.loads(json_str)
                            if "is_relevant" in classification and "reason" in classification:
                                logger.info("Successfully extracted JSON from embedded text")
                                return {
                                    "is_relevant": bool(classification["is_relevant"]),
                                    "reason": str(classification["reason"])
                                }
                    except (json.JSONDecodeError, AttributeError) as extract_error:
                        logger.debug(f"Could not extract JSON from text: {extract_error}")
                    
                    if attempt < max_retries:
                        continue
                    
                    # Final fallback: try to extract boolean from text
                    response_lower = response_text.lower()
                    is_relevant = "true" in response_lower or "yes" in response_lower
                    return {
                        "is_relevant": is_relevant,
                        "reason": "Could not parse detailed reasoning"
                    }
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Error calling Ollama API: {e}")
                if attempt < max_retries:
                    continue
                return {
                    "is_relevant": False,
                    "reason": f"API error: {str(e)}"
                }
            except Exception as e:
                logger.error(f"Unexpected error during classification: {e}")
                if attempt < max_retries:
                    continue
                return {
                    "is_relevant": False,
                    "reason": f"Error: {str(e)}"
                }
        
        # Final fallback
        return {
            "is_relevant": False,
            "reason": "Classification failed after retries"
        }
    
    def safe_move_file(
        self,
        source_path: Path,
        target_dir: Path
    ) -> Path:
        """
        Safely move a file to target directory with collision handling.
        
        If file exists in target, renames to filename_1.ext, filename_2.ext, etc.
        
        Args:
            source_path: Path to source file
            target_dir: Path to target directory
            
        Returns:
            Path where file was moved
            
        Raises:
            IOError: If file cannot be moved
        """
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise IOError(f"Failed to create target directory {target_dir}: {str(e)}") from e
        
        target_path = target_dir / source_path.name
        
        # Handle collision
        if target_path.exists():
            stem = source_path.stem
            suffix = source_path.suffix
            counter = 1
            
            while target_path.exists():
                new_name = f"{stem}_{counter}{suffix}"
                target_path = target_dir / new_name
                counter += 1
                
                # Safety check to prevent infinite loop
                if counter > 10000:
                    raise IOError(f"Too many files with similar names in {target_dir}")
        
        # Move file with error handling
        try:
            shutil.move(str(source_path), str(target_path))
            logger.info(f"Moved {source_path.name} to {target_path}")
        except (IOError, OSError, shutil.Error) as e:
            raise IOError(f"Failed to move {source_path.name} to {target_path}: {str(e)}") from e
        
        return target_path
    
    def process_file(
        self,
        file_path: Path,
        criteria: str,
        target_relevant: Path,
        target_irrelevant: Path,
        max_pages: int = 5
    ) -> Dict[str, Any]:
        """
        Process a single file: extract text, classify, and move.
        
        Args:
            file_path: Path to file to process
            criteria: Classification criteria
            target_relevant: Directory for relevant files
            target_irrelevant: Directory for irrelevant files
            max_pages: Maximum pages to extract (lazy loading)
            
        Returns:
            Dictionary with processing result:
            - filename: str
            - decision: str ("relevant" or "irrelevant")
            - reason: str
            - moved_to: str
            - error: Optional[str]
        """
        filename = file_path.name
        timestamp = datetime.now().isoformat()
        
        try:
            # Read file content with error handling
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
            except IOError as io_error:
                raise IOError(f"Failed to read file {filename}: {str(io_error)}") from io_error
            except Exception as read_error:
                raise Exception(f"Unexpected error reading file {filename}: {str(read_error)}") from read_error
            
            # Extract text with max_pages limit for lazy loading
            try:
                parsed_data = self.document_service.parse_pdf(
                    file_content,
                    filename=filename,
                    max_pages=max_pages
                )
            except ValueError as pdf_error:
                # Re-raise with more context (encrypted PDF, empty file, etc.)
                raise ValueError(f"PDF parsing error for {filename}: {str(pdf_error)}") from pdf_error
            except Exception as parse_error:
                raise Exception(f"Failed to parse PDF {filename}: {str(parse_error)}") from parse_error
            
            # Get text from parsed pages
            pages = parsed_data.get("pages", [])
            text = "\n".join(page.get("text", "") for page in pages)
            
            if not text.strip():
                raise ValueError("No text could be extracted from document")
            
            # Classify document
            classification = self.classify_document(text, criteria)
            
            # Determine target directory
            is_relevant = classification.get("is_relevant", False)
            target_dir = target_relevant if is_relevant else target_irrelevant
            decision = "relevant" if is_relevant else "irrelevant"
            
            # Move file with error handling
            try:
                moved_path = self.safe_move_file(file_path, target_dir)
            except (IOError, OSError) as move_error:
                raise Exception(f"Failed to move file {filename}: {str(move_error)}") from move_error
            
            result = {
                "filename": filename,
                "timestamp": timestamp,
                "decision": decision,
                "reason": classification.get("reason", "No reason provided"),
                "moved_to": str(moved_path.parent.name),
                "error": None
            }
            
            # Add to audit log
            self.audit_log.append(result)
            
            return result
        
        except Exception as e:
            error_msg = f"Error processing {filename}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            result = {
                "filename": filename,
                "timestamp": timestamp,
                "decision": "error",
                "reason": str(e),
                "moved_to": "N/A",
                "error": str(e)
            }
            
            # Add to audit log
            self.audit_log.append(result)
            
            return result
    
    def batch_process(
        self,
        source_folder: str,
        target_relevant: str,
        target_irrelevant: str,
        criteria: str,
        max_pages: int = 5,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Process all files in source folder.
        
        Args:
            source_folder: Path to source folder
            target_relevant: Path to relevant folder
            target_irrelevant: Path to irrelevant folder
            criteria: Classification criteria
            max_pages: Maximum pages to analyze per document
            progress_callback: Optional callback function(current, total, result)
            
        Returns:
            Dictionary with:
            - total_files: int
            - processed: int
            - relevant: int
            - irrelevant: int
            - errors: int
            - audit_log: List[Dict]
        """
        source_path = Path(source_folder)
        target_relevant_path = Path(target_relevant)
        target_irrelevant_path = Path(target_irrelevant)
        
        # Validate paths
        if not source_path.exists():
            raise ValueError(f"Source folder does not exist: {source_folder}")
        
        # Create target directories if they don't exist
        target_relevant_path.mkdir(parents=True, exist_ok=True)
        target_irrelevant_path.mkdir(parents=True, exist_ok=True)
        
        # Find all PDF files (case-insensitive)
        seen_files = set()
        pdf_files = []
        for pattern in self.PDF_PATTERNS:
            for file_path in source_path.glob(pattern):
                if file_path not in seen_files:
                    seen_files.add(file_path)
                    pdf_files.append(file_path)
        
        total_files = len(pdf_files)
        
        logger.info(f"Found {total_files} PDF files to process")
        
        # Reset audit log
        self.audit_log = []
        
        # Process each file
        stats = {
            "total_files": total_files,
            "processed": 0,
            "relevant": 0,
            "irrelevant": 0,
            "errors": 0
        }
        
        for i, file_path in enumerate(pdf_files, 1):
            result = self.process_file(
                file_path,
                criteria,
                target_relevant_path,
                target_irrelevant_path,
                max_pages
            )
            
            # Update stats
            stats["processed"] += 1
            if result["error"]:
                stats["errors"] += 1
            elif result["decision"] == "relevant":
                stats["relevant"] += 1
            elif result["decision"] == "irrelevant":
                stats["irrelevant"] += 1
            
            # Call progress callback
            if progress_callback:
                progress_callback(i, total_files, result)
        
        stats["audit_log"] = self.audit_log
        
        return stats
    
    def export_audit_log(
        self,
        output_path: str,
        format: str = "xlsx"
    ) -> str:
        """
        Export audit log to Excel or CSV file.
        
        Args:
            output_path: Path to output file
            format: Export format ('xlsx' or 'csv')
            
        Returns:
            Path to exported file
        """
        if not self.audit_log:
            raise ValueError("No audit log data to export")
        
        # Create DataFrame
        df = pd.DataFrame(self.audit_log)
        
        # Rename columns for clarity
        df = df.rename(columns={
            "filename": "Filename",
            "timestamp": "Date",
            "decision": "Decision (Yes/No)",
            "reason": "AI Reasoning",
            "moved_to": "Moved To"
        })
        
        # Export
        if format.lower() == "xlsx":
            df.to_excel(output_path, index=False, engine='openpyxl')
        else:
            df.to_csv(output_path, index=False)
        
        logger.info(f"Exported audit log to {output_path}")
        
        return output_path
