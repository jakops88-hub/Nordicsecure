"""
Stress Test for PDF Processing - Memory Leak and Performance Analysis
======================================================================

This script performs a stress test on the DocumentService.parse_pdf() function
to detect memory leaks and measure performance under repeated execution.

Features:
- Generates dummy PDF objects for testing
- Executes PDF processing in a loop with multiple iterations
- Monitors RAM usage using psutil to detect memory leaks
- Tracks execution time for every 5th file with ETA calculation
- Reports comprehensive statistics including percentiles (p50, p90, p95, p99)
- Provides detailed memory analysis and leak detection
- Supports Ollama port fallback (11435 → 11434) if needed
- Generates detailed report file with all statistics
- Shows real-time progress with estimated time remaining

Configuration:
- Default: 50 PDFs x 1 iteration = 50 total files
- Customizable through PDFStressTest constructor

Run with: python backend/test_pdf_stress.py

Note: If Ollama connection fails on port 11435, the system will automatically
      fall back to the default port 11434 (via OLLAMA_HOST environment variable).
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


class PDFStressTest:
    """Stress test runner for PDF processing performance and memory analysis."""
    
    # Memory leak detection thresholds
    MEMORY_LEAK_THRESHOLD_MB = 5.0  # MB - significant memory growth threshold
    SLOPE_THRESHOLD_MB = 0.5  # MB per sample - linear growth threshold
    
    def __init__(self, num_pdfs: int = 50, iterations: int = 3):
        """
        Initialize stress test.
        
        Args:
            num_pdfs: Number of dummy PDF files to generate
            iterations: Number of times to process all PDFs
        """
        self.num_pdfs = num_pdfs
        self.iterations = iterations
        self.process = psutil.Process()
        self.document_service = None
        self.dummy_pdfs: List[Dict[str, Any]] = []
        
        # Statistics tracking for all steps
        self.stats = {
            'pdf_generation': [],
            'text_extraction': [],
            'ocr_processing': [],
            'embedding_generation': [],
            'total_processing': [],
            'memory_samples': [],
            'errors': []
        }
        
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
        """Initialize document service and generate dummy PDFs."""
        print("=" * 70)
        print("PDF PROCESSING STRESS TEST - MEMORY LEAK & PERFORMANCE ANALYSIS")
        print("=" * 70)
        print()
        
        print(f"Configuration:")
        print(f"  - Number of PDFs: {self.num_pdfs}")
        print(f"  - Iterations: {self.iterations}")
        print(f"  - Total files to process: {self.num_pdfs * self.iterations}")
        
        # Check Ollama port configuration
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        print(f"  - Ollama Host: {ollama_host}")
        if "11435" in ollama_host:
            print(f"    ⚠️  Warning: Port 11435 detected. Will fallback to 11434 if connection fails.")
        print()
        
        # Initialize document service (without embedding model for faster testing)
        print("Initializing DocumentService...")
        self.document_service = DocumentService(collection=None)
        print("✓ DocumentService initialized")
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
        """Execute the stress test and monitor performance with detailed statistics."""
        print("=" * 70)
        print("STARTING STRESS TEST")
        print("=" * 70)
        print()
        
        # Record initial memory
        gc.collect()  # Force garbage collection before starting
        initial_memory = self.get_memory_usage_mb()
        print(f"Initial memory usage: {initial_memory:.2f} MB")
        print()
        
        # Track memory samples
        memory_samples = [initial_memory]
        self.stats['memory_samples'].append(initial_memory)
        execution_times = []
        
        # Detailed step timing
        step_timings = {
            'pdf_parsing': [],
            'text_extraction': [],
            'processing': []
        }
        
        total_files = self.num_pdfs * self.iterations
        files_processed = 0
        successful_files = 0
        failed_files = 0
        
        # Overall timing
        overall_start = time.time()
        
        # Main stress test loop
        for iteration in range(self.iterations):
            print(f"Iteration {iteration + 1}/{self.iterations}")
            print("-" * 50)
            
            iteration_start = time.time()
            
            for pdf_idx, pdf in enumerate(self.dummy_pdfs):
                files_processed += 1
                
                # Track execution time for each step
                start_time = time.time()
                step_start = start_time
                
                try:
                    # Execute PDF parsing with detailed timing
                    result = self.document_service.parse_pdf(
                        file=pdf["data"],
                        filename=pdf["filename"]
                    )
                    
                    # Total execution time
                    execution_time = time.time() - start_time
                    execution_times.append(execution_time)
                    self.stats['total_processing'].append(execution_time)
                    successful_files += 1
                    
                    # Print timing for every 5th file
                    if files_processed % 5 == 0:
                        current_memory = self.get_memory_usage_mb()
                        memory_samples.append(current_memory)
                        self.stats['memory_samples'].append(current_memory)
                        memory_delta = current_memory - initial_memory
                        
                        # Calculate progress percentage
                        progress_pct = (files_processed / total_files) * 100
                        
                        # Estimate time remaining
                        elapsed = time.time() - overall_start
                        avg_time_per_file = elapsed / files_processed
                        remaining_files = total_files - files_processed
                        eta_seconds = remaining_files * avg_time_per_file
                        eta_minutes = eta_seconds / 60
                        
                        print(
                            f"  [{progress_pct:5.1f}%] File {files_processed}/{total_files}: "
                            f"{execution_time:.3f}s | "
                            f"Memory: {current_memory:.2f} MB "
                            f"(Δ {memory_delta:+.2f} MB) | "
                            f"ETA: {eta_minutes:.1f}m"
                        )
                    
                except Exception as e:
                    failed_files += 1
                    self.stats['errors'].append({
                        'file': pdf['filename'],
                        'error': str(e),
                        'iteration': iteration + 1
                    })
                    print(f"  ERROR processing {pdf['filename']}: {e}")
                    continue
            
            # Force garbage collection after each iteration
            gc.collect()
            
            iteration_time = time.time() - iteration_start
            iteration_memory = self.get_memory_usage_mb()
            memory_samples.append(iteration_memory)
            self.stats['memory_samples'].append(iteration_memory)
            
            print(f"  End of iteration memory: {iteration_memory:.2f} MB")
            print(f"  Iteration time: {iteration_time:.2f} seconds")
            print()
        
        # Final memory check
        gc.collect()
        final_memory = self.get_memory_usage_mb()
        memory_samples.append(final_memory)
        self.stats['memory_samples'].append(final_memory)
        
        # Calculate overall stats
        overall_time = time.time() - overall_start
        
        # Analyze results
        self.print_results(
            initial_memory=initial_memory,
            final_memory=final_memory,
            memory_samples=memory_samples,
            execution_times=execution_times,
            files_processed=files_processed,
            successful_files=successful_files,
            failed_files=failed_files,
            overall_time=overall_time
        )
    
    def print_results(
        self,
        initial_memory: float,
        final_memory: float,
        memory_samples: List[float],
        execution_times: List[float],
        files_processed: int,
        successful_files: int,
        failed_files: int,
        overall_time: float
    ):
        """Print stress test results and analysis with comprehensive statistics."""
        print()
        print("=" * 70)
        print("STRESS TEST RESULTS - COMPREHENSIVE STATISTICS")
        print("=" * 70)
        print()
        
        # Performance metrics
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
        min_time = min(execution_times) if execution_times else 0
        max_time = max(execution_times) if execution_times else 0
        
        # Calculate percentiles
        if execution_times:
            sorted_times = sorted(execution_times)
            p50 = sorted_times[len(sorted_times) // 2]
            p90 = sorted_times[int(len(sorted_times) * 0.9)]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) >= 100 else max_time
        else:
            p50 = p90 = p95 = p99 = 0
        
        print(f"📊 Overall Performance Metrics:")
        print(f"  ├─ Total runtime: {overall_time:.2f} seconds ({overall_time/60:.2f} minutes)")
        print(f"  ├─ Files processed: {files_processed}")
        print(f"  ├─ Successful: {successful_files} ({successful_files/files_processed*100:.1f}%)")
        print(f"  ├─ Failed: {failed_files} ({failed_files/files_processed*100:.1f}%)" if failed_files > 0 else f"  ├─ Failed: 0 (0.0%)")
        print(f"  └─ Throughput: {files_processed/overall_time:.2f} files/second")
        print()
        
        print(f"⏱️  Execution Time Statistics:")
        print(f"  ├─ Average time per file: {avg_time:.3f} seconds")
        print(f"  ├─ Median (p50): {p50:.3f} seconds")
        print(f"  ├─ Min time: {min_time:.3f} seconds")
        print(f"  ├─ Max time: {max_time:.3f} seconds")
        print(f"  ├─ p90: {p90:.3f} seconds")
        print(f"  ├─ p95: {p95:.3f} seconds")
        print(f"  ├─ p99: {p99:.3f} seconds")
        print(f"  └─ Total processing time: {sum(execution_times):.2f} seconds")
        print()
        
        # Memory analysis
        memory_delta = final_memory - initial_memory
        memory_growth_percent = (memory_delta / initial_memory) * 100 if initial_memory > 0 else 0
        peak_memory = max(memory_samples)
        min_memory = min(memory_samples)
        avg_memory = sum(memory_samples) / len(memory_samples)
        
        print(f"💾 Memory Analysis:")
        print(f"  ├─ Initial memory: {initial_memory:.2f} MB")
        print(f"  ├─ Final memory: {final_memory:.2f} MB")
        print(f"  ├─ Memory delta: {memory_delta:+.2f} MB ({memory_growth_percent:+.1f}%)")
        print(f"  ├─ Peak memory: {peak_memory:.2f} MB")
        print(f"  ├─ Min memory: {min_memory:.2f} MB")
        print(f"  ├─ Average memory: {avg_memory:.2f} MB")
        print(f"  └─ Memory per file (avg): {memory_delta/files_processed:.3f} MB" if files_processed > 0 else f"  └─ Memory per file (avg): N/A")
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
            
            print(f"🔍 Memory Leak Detection:")
            print(f"  ├─ Memory growth rate: {slope:.4f} MB per sample")
            
            # Detect memory leak
            # If memory grows more than threshold and shows consistent upward trend
            
            if memory_delta > self.MEMORY_LEAK_THRESHOLD_MB and slope > self.SLOPE_THRESHOLD_MB:
                print(f"  └─ ⚠️  MEMORY LEAK DETECTED!")
                print(f"     Memory grew by {memory_delta:.2f} MB and did not stabilize.")
                print(f"     Slope indicates consistent growth: {slope:.4f} MB per sample.")
                print()
            elif memory_delta > self.MEMORY_LEAK_THRESHOLD_MB:
                print(f"  └─ ⚠️  WARNING: Significant memory growth detected")
                print(f"     Memory grew by {memory_delta:.2f} MB, but growth rate is not linear.")
                print(f"     This might be normal caching behavior.")
                print()
            else:
                print(f"  └─ ✓ Memory appears stable - No significant memory leak detected")
                print(f"     Memory growth is within acceptable limits ({memory_delta:.2f} MB).")
                print()
        
        # Error analysis
        if self.stats['errors']:
            print(f"❌ Errors Encountered ({len(self.stats['errors'])}):")
            for idx, error in enumerate(self.stats['errors'][:5], 1):  # Show first 5 errors
                print(f"  {idx}. {error['file']} (Iteration {error['iteration']}): {error['error']}")
            if len(self.stats['errors']) > 5:
                print(f"  ... and {len(self.stats['errors']) - 5} more errors")
            print()
        
        # Summary
        print("=" * 70)
        print("📋 SUMMARY")
        print("=" * 70)
        print(f"✓ Processed {files_processed} files in {overall_time:.2f} seconds")
        print(f"✓ Success rate: {successful_files/files_processed*100:.1f}% ({successful_files}/{files_processed})")
        print(f"✓ Average time per file: {avg_time:.3f} seconds")
        print(f"✓ Throughput: {files_processed/overall_time:.2f} files/second")
        
        if memory_delta > 5.0:
            print(f"⚠️  Memory grew by {memory_delta:.2f} MB - Review for potential leaks")
        else:
            print(f"✓ Memory stable: {memory_delta:+.2f} MB change")
        
        if failed_files > 0:
            print(f"⚠️  {failed_files} files failed processing")
        
        print()
        
        # Save detailed statistics to file
        self.save_statistics_report(
            overall_time=overall_time,
            files_processed=files_processed,
            successful_files=successful_files,
            failed_files=failed_files,
            execution_times=execution_times,
            memory_samples=memory_samples,
            initial_memory=initial_memory,
            final_memory=final_memory
        )
    
    def save_statistics_report(
        self,
        overall_time: float,
        files_processed: int,
        successful_files: int,
        failed_files: int,
        execution_times: List[float],
        memory_samples: List[float],
        initial_memory: float,
        final_memory: float
    ):
        """Save detailed statistics report to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"stress_test_report_{timestamp}.txt"
            
            with open(report_filename, 'w') as f:
                f.write("=" * 70 + "\n")
                f.write("STRESS TEST DETAILED REPORT\n")
                f.write("=" * 70 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Configuration: {self.num_pdfs} PDFs x {self.iterations} iterations\n")
                f.write("\n")
                
                # Overall metrics
                f.write("OVERALL METRICS:\n")
                f.write(f"  Total runtime: {overall_time:.2f} seconds ({overall_time/60:.2f} minutes)\n")
                f.write(f"  Files processed: {files_processed}\n")
                f.write(f"  Successful: {successful_files}\n")
                f.write(f"  Failed: {failed_files}\n")
                f.write(f"  Throughput: {files_processed/overall_time:.2f} files/second\n")
                f.write("\n")
                
                # Execution times
                if execution_times:
                    sorted_times = sorted(execution_times)
                    avg_time = sum(execution_times) / len(execution_times)
                    p50 = sorted_times[len(sorted_times) // 2]
                    p90 = sorted_times[int(len(sorted_times) * 0.9)]
                    p95 = sorted_times[int(len(sorted_times) * 0.95)]
                    
                    f.write("EXECUTION TIME STATISTICS:\n")
                    f.write(f"  Average: {avg_time:.3f} seconds\n")
                    f.write(f"  Median (p50): {p50:.3f} seconds\n")
                    f.write(f"  Min: {min(execution_times):.3f} seconds\n")
                    f.write(f"  Max: {max(execution_times):.3f} seconds\n")
                    f.write(f"  p90: {p90:.3f} seconds\n")
                    f.write(f"  p95: {p95:.3f} seconds\n")
                    f.write("\n")
                
                # Memory analysis
                memory_delta = final_memory - initial_memory
                f.write("MEMORY STATISTICS:\n")
                f.write(f"  Initial: {initial_memory:.2f} MB\n")
                f.write(f"  Final: {final_memory:.2f} MB\n")
                f.write(f"  Delta: {memory_delta:+.2f} MB\n")
                f.write(f"  Peak: {max(memory_samples):.2f} MB\n")
                f.write(f"  Average: {sum(memory_samples)/len(memory_samples):.2f} MB\n")
                f.write("\n")
                
                # All execution times
                f.write("DETAILED EXECUTION TIMES (all files):\n")
                for idx, exec_time in enumerate(execution_times, 1):
                    f.write(f"  File {idx}: {exec_time:.3f}s\n")
                f.write("\n")
                
                # Errors
                if self.stats['errors']:
                    f.write(f"ERRORS ({len(self.stats['errors'])}):\n")
                    for error in self.stats['errors']:
                        f.write(f"  {error['file']} (Iteration {error['iteration']}): {error['error']}\n")
                    f.write("\n")
                
                f.write("=" * 70 + "\n")
            
            print(f"📄 Detailed report saved to: {report_filename}")
            
        except Exception as e:
            print(f"⚠️  Failed to save detailed report: {e}")


def main():
    """Main entry point for stress test."""
    try:
        # Create stress test instance
        # Configured for 50 PDFs as requested
        stress_test = PDFStressTest(num_pdfs=50, iterations=1)
        
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
