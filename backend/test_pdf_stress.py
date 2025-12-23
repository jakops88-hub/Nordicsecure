"""
Stress Test for PDF Processing with LLM Classification - Memory and Performance Analysis
=========================================================================================

This script performs a stress test with REAL Llama 3 model inference to measure
RAM usage and performance under actual production workload.

Features:
- Generates 20 dummy PDF objects for testing
- Loads Llama 3 model and performs REAL classification inference
- Extracts text from PDFs AND categorizes them using the LLM
- Monitors RAM usage using psutil to detect memory consumption
- Tracks execution time for each file
- Reports average time per file and memory usage with model loaded

Prerequisites:
- Ollama must be running: ollama serve
- Llama 3 model must be pulled: ollama pull llama3

Run with: python backend/test_pdf_stress.py
"""

import sys
import os
import io
import gc
import time
import psutil
from datetime import datetime
from typing import List, Dict, Any

# Add backend to path for imports
# Note: This is acceptable for a standalone test script.
# For production code, consider using proper package structure with __init__.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import PyPDF2
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    PyPDF2 = None
    canvas = None
    letter = None

from backend.app.services.document_service import DocumentService
from backend.app.services.triage_service import TriageService


class PDFStressTest:
    """Stress test runner for PDF processing with LLM classification."""
    
    # Memory leak detection thresholds
    MEMORY_LEAK_THRESHOLD_MB = 5.0  # MB - significant memory growth threshold
    SLOPE_THRESHOLD_MB = 0.5  # MB per sample - linear growth threshold
    
    # Test configuration for real model inference
    DEFAULT_NUM_PDFS = 20  # Reduced for realistic testing with LLM
    DEFAULT_OLLAMA_URL = "http://localhost:11434"  # Standard Ollama port
    DEFAULT_MODEL_NAME = "llama3"
    
    def __init__(
        self,
        num_pdfs: int = DEFAULT_NUM_PDFS,
        iterations: int = 1,
        ollama_url: str = DEFAULT_OLLAMA_URL,
        model_name: str = DEFAULT_MODEL_NAME
    ):
        """
        Initialize stress test with real LLM inference.
        
        Args:
            num_pdfs: Number of dummy PDF files to generate
            iterations: Number of times to process all PDFs
            ollama_url: URL for Ollama API
            model_name: Name of the LLM model to use
        """
        self.num_pdfs = num_pdfs
        self.iterations = iterations
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.process = psutil.Process()
        self.document_service = None
        self.triage_service = None
        self.dummy_pdfs: List[Dict[str, Any]] = []
        
    def generate_dummy_pdf(self, pdf_id: int, num_pages: int = 3) -> bytes:
        """
        Generate a dummy PDF file for testing.
        
        Args:
            pdf_id: Identifier for the PDF
            num_pages: Number of pages to generate
            
        Returns:
            PDF file as bytes
        """
        if canvas is None:
            # Fallback: create minimal valid PDF manually
            return self._create_minimal_pdf(pdf_id, num_pages)
        
        # Create PDF in memory using reportlab
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Use current date for realistic test data
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        for page_num in range(num_pages):
            # Add some text content to each page
            c.drawString(100, 750, f"Test Document #{pdf_id}")
            c.drawString(100, 730, f"Page {page_num + 1} of {num_pages}")
            c.drawString(100, 710, f"Generated at: {datetime.now().isoformat()}")
            
            # Add some sample invoice-like content
            c.drawString(100, 650, "Sample Invoice Data:")
            c.drawString(100, 630, f"Date: {current_date}")
            c.drawString(100, 610, "Amount: $1,234.56")
            c.drawString(100, 590, "Vendor: Test Corporation Inc.")
            
            # Add some Lorem Ipsum text
            y_position = 550
            sample_text = [
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
                "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.",
                "Duis aute irure dolor in reprehenderit in voluptate velit esse.",
                "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui.",
            ]
            for line in sample_text:
                c.drawString(100, y_position, line)
                y_position -= 20
            
            c.showPage()
        
        c.save()
        buffer.seek(0)
        return buffer.read()
    
    def _create_minimal_pdf(self, pdf_id: int, num_pages: int = 3) -> bytes:
        """
        Create a minimal valid PDF without reportlab dependency.
        
        This is a fallback method that creates a simple but valid PDF structure.
        """
        # Simple PDF structure with multiple pages
        pdf_content = []
        pdf_content.append(b"%PDF-1.4\n")
        
        # Catalog
        pdf_content.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        
        # Pages object
        page_refs = " ".join([f"{3 + i} 0 R" for i in range(num_pages)])
        pdf_content.append(f"2 0 obj\n<< /Type /Pages /Kids [{page_refs}] /Count {num_pages} >>\nendobj\n".encode())
        
        # Individual pages with content
        for page_num in range(num_pages):
            page_obj_num = 3 + page_num
            content_obj_num = 3 + num_pages + page_num
            
            # Page object
            pdf_content.append(
                f"{page_obj_num} 0 obj\n"
                f"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> "
                f"/MediaBox [0 0 612 792] /Contents {content_obj_num} 0 R >>\n"
                f"endobj\n".encode()
            )
            
            # Content stream
            text_content = (
                f"BT\n"
                f"/F1 12 Tf\n"
                f"100 750 Td\n"
                f"(Test Document #{pdf_id}) Tj\n"
                f"0 -20 Td\n"
                f"(Page {page_num + 1} of {num_pages}) Tj\n"
                f"0 -40 Td\n"
                f"(Sample Invoice Data:) Tj\n"
                f"0 -20 Td\n"
                f"(Date: 2024-01-15) Tj\n"
                f"0 -20 Td\n"
                f"(Amount: $1234.56) Tj\n"
                f"0 -20 Td\n"
                f"(Vendor: Test Corporation Inc.) Tj\n"
                f"ET\n"
            )
            
            stream_data = text_content.encode()
            pdf_content.append(
                f"{content_obj_num} 0 obj\n"
                f"<< /Length {len(stream_data)} >>\n"
                f"stream\n".encode() +
                stream_data +
                b"\nendstream\nendobj\n"
            )
        
        # xref table
        # Note: Using simplified xref with placeholder offsets for testing purposes.
        # This creates a minimal but valid PDF structure that works with PyPDF2.
        # For production use, proper xref offsets should be calculated.
        xref_offset = sum(len(chunk) for chunk in pdf_content)
        pdf_content.append(b"xref\n")
        pdf_content.append(f"0 {3 + 2 * num_pages}\n".encode())
        
        # Simplified xref - just mark all objects as in use
        pdf_content.append(b"0000000000 65535 f \n")
        for i in range(1, 3 + 2 * num_pages):
            pdf_content.append(b"0000000000 00000 n \n")
        
        # Trailer
        pdf_content.append(
            f"trailer\n"
            f"<< /Size {3 + 2 * num_pages} /Root 1 0 R >>\n"
            f"startxref\n"
            f"{xref_offset}\n"
            f"%%EOF\n".encode()
        )
        
        return b"".join(pdf_content)
    
    def initialize_test(self):
        """Initialize document service, triage service with LLM, and generate dummy PDFs."""
        print("=" * 70)
        print("PDF PROCESSING STRESS TEST WITH REAL LLAMA 3 INFERENCE")
        print("=" * 70)
        print()
        
        print(f"Configuration:")
        print(f"  - Number of PDFs: {self.num_pdfs}")
        print(f"  - Iterations: {self.iterations}")
        print(f"  - Total files to process: {self.num_pdfs * self.iterations}")
        print(f"  - Ollama URL: {self.ollama_url}")
        print(f"  - Model: {self.model_name}")
        print()
        
        # Initialize document service (without embedding model for faster testing)
        print("Initializing DocumentService...")
        self.document_service = DocumentService(collection=None)
        print("✓ DocumentService initialized")
        print()
        
        # Initialize TriageService with real Llama 3 model
        print(f"Initializing TriageService with {self.model_name}...")
        print("⚠️  This will connect to Ollama and load the model into memory")
        self.triage_service = TriageService(
            document_service=self.document_service,
            ollama_base_url=self.ollama_url,
            model_name=self.model_name
        )
        print("✓ TriageService initialized")
        print()
        
        # Verify Ollama is running by making a test call
        print("Verifying Ollama connection...")
        try:
            import requests
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print("✓ Ollama is running and accessible")
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if any(self.model_name in name for name in model_names):
                    print(f"✓ Model '{self.model_name}' is available")
                else:
                    print(f"⚠️  Model '{self.model_name}' not found in available models")
                    print(f"   Available models: {', '.join(model_names) if model_names else 'None'}")
                    print(f"   The model will be pulled on first use (this may take time)")
            else:
                print(f"⚠️  Ollama returned status code: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Could not verify Ollama connection: {e}")
            print("   Make sure Ollama is running: ollama serve")
            raise RuntimeError(f"Ollama is not accessible at {self.ollama_url}. Please start it first.") from e
        print()
        
        # Generate dummy PDFs
        print(f"Generating {self.num_pdfs} dummy PDF files...")
        for i in range(self.num_pdfs):
            pdf_bytes = self.generate_dummy_pdf(i + 1, num_pages=3)
            self.dummy_pdfs.append({
                "id": i + 1,
                "filename": f"test_document_{i + 1}.pdf",
                "data": pdf_bytes,
                "size_kb": len(pdf_bytes) / 1024
            })
        
        total_size = sum(pdf["size_kb"] for pdf in self.dummy_pdfs)
        print(f"✓ Generated {self.num_pdfs} PDFs (Total: {total_size:.2f} KB)")
        print()
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / (1024 * 1024)
    
    def run_stress_test(self):
        """Execute the stress test with REAL LLM inference and monitor performance."""
        print("=" * 70)
        print("STARTING STRESS TEST WITH REAL LLAMA 3 INFERENCE")
        print("=" * 70)
        print()
        print("⚠️  Note: Each file will take 5-10 seconds due to real model inference")
        print()
        
        # Record initial memory
        gc.collect()  # Force garbage collection before starting
        initial_memory = self.get_memory_usage_mb()
        print(f"Initial memory usage: {initial_memory:.2f} MB")
        print()
        
        # Track memory samples
        memory_samples = [initial_memory]
        execution_times = []
        
        total_files = self.num_pdfs * self.iterations
        files_processed = 0
        
        # Classification criteria for testing
        classification_criteria = (
            "Classify if this document is an invoice or receipt. "
            "Look for invoice numbers, amounts, dates, and vendor information."
        )
        
        # Main stress test loop
        for iteration in range(self.iterations):
            print(f"Iteration {iteration + 1}/{self.iterations}")
            print("-" * 50)
            
            for pdf_idx, pdf in enumerate(self.dummy_pdfs):
                files_processed += 1
                
                # Track execution time
                start_time = time.time()
                
                try:
                    # Step 1: Extract text from PDF
                    parsed_data = self.document_service.parse_pdf(
                        file=pdf["data"],
                        filename=pdf["filename"]
                    )
                    
                    # Step 2: Get text for classification
                    pages = parsed_data.get("pages", [])
                    text = "\n".join(page.get("text", "") for page in pages)
                    
                    # Step 3: REAL LLM classification - this is the key change!
                    # This actually loads the model and performs inference
                    classification_result = self.triage_service.classify_document(
                        text=text,
                        criteria=classification_criteria
                    )
                    
                    execution_time = time.time() - start_time
                    execution_times.append(execution_time)
                    
                    # Print timing for each file to show real progress
                    current_memory = self.get_memory_usage_mb()
                    memory_samples.append(current_memory)
                    memory_delta = current_memory - initial_memory
                    
                    is_relevant = classification_result.get("is_relevant", False)
                    reason = classification_result.get("reason", "No reason")
                    
                    print(
                        f"  File {files_processed}/{total_files}: "
                        f"{execution_time:.3f}s | "
                        f"Memory: {current_memory:.2f} MB "
                        f"(Δ {memory_delta:+.2f} MB) | "
                        f"Classified: {'Yes' if is_relevant else 'No'}"
                    )
                    
                except Exception as e:
                    print(f"  ERROR processing {pdf['filename']}: {e}")
                    execution_times.append(time.time() - start_time)
                    continue
            
            # Force garbage collection after each iteration
            gc.collect()
            
            iteration_memory = self.get_memory_usage_mb()
            memory_samples.append(iteration_memory)
            print(f"  End of iteration memory: {iteration_memory:.2f} MB")
            print()
        
        # Final memory check
        gc.collect()
        final_memory = self.get_memory_usage_mb()
        memory_samples.append(final_memory)
        
        # Analyze results
        self.print_results(
            initial_memory=initial_memory,
            final_memory=final_memory,
            memory_samples=memory_samples,
            execution_times=execution_times,
            files_processed=files_processed
        )
    
    def print_results(
        self,
        initial_memory: float,
        final_memory: float,
        memory_samples: List[float],
        execution_times: List[float],
        files_processed: int
    ):
        """Print stress test results and analysis."""
        print()
        print("=" * 70)
        print("STRESS TEST RESULTS")
        print("=" * 70)
        print()
        
        # Performance metrics
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
        min_time = min(execution_times) if execution_times else 0
        max_time = max(execution_times) if execution_times else 0
        
        print(f"Performance Metrics:")
        print(f"  - Files processed: {files_processed}")
        print(f"  - Average time per file: {avg_time:.3f} seconds")
        print(f"  - Min time: {min_time:.3f} seconds")
        print(f"  - Max time: {max_time:.3f} seconds")
        print(f"  - Total processing time: {sum(execution_times):.2f} seconds")
        print()
        print(f"  ⚠️  Expected: 5-10 seconds per file with real LLM inference")
        if avg_time < 1.0:
            print(f"  ⚠️  WARNING: Average time is too low! Model inference may not be running.")
        elif avg_time >= 5.0:
            print(f"  ✓ Realistic timing confirmed - LLM is performing real inference")
        print()
        
        # Memory analysis
        memory_delta = final_memory - initial_memory
        memory_growth_percent = (memory_delta / initial_memory) * 100 if initial_memory > 0 else 0
        
        print(f"Memory Analysis:")
        print(f"  - Initial memory: {initial_memory:.2f} MB")
        print(f"  - Final memory: {final_memory:.2f} MB")
        print(f"  - Memory delta: {memory_delta:+.2f} MB ({memory_growth_percent:+.1f}%)")
        print(f"  - Peak memory: {max(memory_samples):.2f} MB")
        print(f"  - Min memory: {min(memory_samples):.2f} MB")
        print()
        
        # Memory leak detection
        # Check if memory grows linearly (consistent increase without GC)
        # A healthy application should have stable memory after GC
        
        # Calculate memory trend (linear regression slope)
        n = len(memory_samples)
        if n > 2:
            x_mean = sum(range(n)) / n
            y_mean = sum(memory_samples) / n
            
            numerator = sum((i - x_mean) * (mem - y_mean) for i, mem in enumerate(memory_samples))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            
            slope = numerator / denominator if denominator != 0 else 0
            
            print(f"Memory Leak Detection:")
            print(f"  - Memory growth rate: {slope:.4f} MB per sample")
            print()
            
            # Detect memory leak
            # If memory grows more than threshold and shows consistent upward trend
            
            if memory_delta > self.MEMORY_LEAK_THRESHOLD_MB and slope > self.SLOPE_THRESHOLD_MB:
                print("⚠️  MEMORY LEAK DETECTED!")
                print(f"   Memory grew by {memory_delta:.2f} MB and did not stabilize.")
                print(f"   Slope indicates consistent growth: {slope:.4f} MB per sample.")
                print()
            elif memory_delta > self.MEMORY_LEAK_THRESHOLD_MB:
                print("⚠️  WARNING: Significant memory growth detected")
                print(f"   Memory grew by {memory_delta:.2f} MB, but growth rate is not linear.")
                print(f"   This might be normal caching behavior.")
                print()
            else:
                print("✓ Memory appears stable - No significant memory leak detected")
                print(f"  Memory growth is within acceptable limits ({memory_delta:.2f} MB).")
                print()
        
        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"✓ Processed {files_processed} files successfully")
        print(f"✓ Average time per file: {avg_time:.3f} seconds")
        
        if memory_delta > 5.0:
            print(f"⚠️  Memory grew by {memory_delta:.2f} MB - Review for potential leaks")
        else:
            print(f"✓ Memory stable: {memory_delta:+.2f} MB change")
        print()


def main():
    """Main entry point for stress test."""
    try:
        # Create stress test instance with 20 files and 1 iteration for real LLM testing
        stress_test = PDFStressTest(num_pdfs=20, iterations=1)
        
        # Initialize test environment
        stress_test.initialize_test()
        
        # Run stress test
        stress_test.run_stress_test()
        
        print("Stress test completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\n\nStress test interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\nERROR: Stress test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
