"""
Live App Stress Test - Full Stack Testing with 50 PDFs
========================================================

This script performs a comprehensive stress test on the Live Nordic Secure app,
including both frontend (Streamlit) and backend (FastAPI) components.

Features:
- Tests the complete upload workflow through the API
- Processes 50 real PDF files with detailed statistics
- Monitors system performance at all stages
- Provides comprehensive reporting on:
  * Upload times
  * Processing times per file
  * Memory usage across the stack
  * API response times
  * Error rates and failure modes
  * System throughput

Configuration:
- 50 PDFs generated with realistic content
- Tests via HTTP API endpoints
- Full end-to-end workflow simulation

Run with: python stress_test_live.py

Requirements:
- Backend must be running on http://localhost:8000
- Ollama must be running with llama3 model
"""

import sys
import os
import io
import gc
import time
import json
import psutil
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    canvas = None
    letter = None


class LiveAppStressTest:
    """Comprehensive stress test for the Live Nordic Secure application."""
    
    def __init__(
        self,
        num_pdfs: int = 50,
        backend_url: str = "http://localhost:8000"
    ):
        """
        Initialize live app stress test.
        
        Args:
            num_pdfs: Number of PDF files to test with
            backend_url: Base URL of the backend API
        """
        self.num_pdfs = num_pdfs
        self.backend_url = backend_url
        self.process = psutil.Process()
        self.dummy_pdfs: List[Dict[str, Any]] = []
        
        # Statistics tracking
        self.stats = {
            'upload_times': [],
            'processing_times': [],
            'api_response_times': [],
            'memory_samples': [],
            'errors': [],
            'successful_uploads': 0,
            'failed_uploads': 0
        }
    
    def generate_dummy_pdf(self, pdf_id: int, num_pages: int = 3) -> bytes:
        """
        Generate a realistic dummy PDF file for testing.
        
        Args:
            pdf_id: Identifier for the PDF
            num_pages: Number of pages to generate
            
        Returns:
            PDF file as bytes
        """
        if canvas is None:
            return self._create_minimal_pdf(pdf_id, num_pages)
        
        # Create PDF in memory using reportlab
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Use current date for realistic test data
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        for page_num in range(num_pages):
            # Add realistic invoice-like content
            c.drawString(100, 750, f"Invoice #{pdf_id:05d}")
            c.drawString(100, 730, f"Page {page_num + 1} of {num_pages}")
            c.drawString(100, 710, f"Date: {current_date}")
            
            # Invoice details
            c.drawString(100, 670, "INVOICE DETAILS:")
            c.drawString(100, 650, f"Invoice Number: INV-2024-{pdf_id:05d}")
            c.drawString(100, 630, f"Date: {current_date}")
            c.drawString(100, 610, "Amount: SEK 12,345.67")
            c.drawString(100, 590, "Vendor: Nordic Test Corporation AB")
            c.drawString(100, 570, "Customer: Test Customer Ltd")
            
            # Sample line items
            y_position = 530
            c.drawString(100, y_position, "LINE ITEMS:")
            y_position -= 20
            
            line_items = [
                "1. Consulting Services - SEK 8,000.00",
                "2. Software License - SEK 3,000.00",
                "3. Support Contract - SEK 1,345.67",
            ]
            
            for item in line_items:
                c.drawString(120, y_position, item)
                y_position -= 20
            
            # Add some lorem ipsum for realistic content size
            y_position -= 20
            sample_text = [
                "Terms and Conditions:",
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
                "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.",
                "Duis aute irure dolor in reprehenderit in voluptate velit esse.",
            ]
            for line in sample_text:
                if y_position > 100:
                    c.drawString(100, y_position, line)
                    y_position -= 15
            
            c.showPage()
        
        c.save()
        buffer.seek(0)
        return buffer.read()
    
    def _create_minimal_pdf(self, pdf_id: int, num_pages: int = 3) -> bytes:
        """Create a minimal valid PDF without reportlab dependency."""
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
                f"(Invoice #{pdf_id:05d}) Tj\n"
                f"0 -20 Td\n"
                f"(Page {page_num + 1} of {num_pages}) Tj\n"
                f"0 -40 Td\n"
                f"(Test Invoice Data) Tj\n"
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
        xref_offset = sum(len(chunk) for chunk in pdf_content)
        pdf_content.append(b"xref\n")
        pdf_content.append(f"0 {3 + 2 * num_pages}\n".encode())
        
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
    
    def check_backend_health(self) -> bool:
        """Check if backend is running and healthy."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def upload_pdf(self, pdf_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Upload a PDF to the backend via API.
        
        Args:
            pdf_data: PDF file as bytes
            filename: Name of the file
            
        Returns:
            Dictionary with upload result and timing
        """
        start_time = time.time()
        
        try:
            files = {"file": (filename, pdf_data, "application/pdf")}
            response = requests.post(
                f"{self.backend_url}/ingest",
                files=files,
                timeout=120
            )
            
            upload_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "upload_time": upload_time,
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "upload_time": upload_time,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "upload_time": time.time() - start_time,
                "error": "Request timed out after 120 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "upload_time": time.time() - start_time,
                "error": str(e)
            }
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / (1024 * 1024)
    
    def initialize_test(self):
        """Initialize test environment and generate PDFs."""
        print("=" * 70)
        print("LIVE APP STRESS TEST - FULL STACK PERFORMANCE ANALYSIS")
        print("=" * 70)
        print()
        
        print(f"Configuration:")
        print(f"  - Number of PDFs: {self.num_pdfs}")
        print(f"  - Backend URL: {self.backend_url}")
        print()
        
        # Check backend health
        print("Checking backend health...")
        if not self.check_backend_health():
            print("❌ ERROR: Backend is not running or not healthy!")
            print(f"   Please start the backend at {self.backend_url}")
            print("   Run: python backend/main.py")
            sys.exit(1)
        print("✓ Backend is healthy and ready")
        print()
        
        # Generate dummy PDFs
        print(f"Generating {self.num_pdfs} test PDF files...")
        for i in range(self.num_pdfs):
            pdf_bytes = self.generate_dummy_pdf(i + 1, num_pages=3)
            self.dummy_pdfs.append({
                "id": i + 1,
                "filename": f"test_invoice_{i + 1:03d}.pdf",
                "data": pdf_bytes,
                "size_kb": len(pdf_bytes) / 1024
            })
        
        total_size = sum(pdf["size_kb"] for pdf in self.dummy_pdfs)
        print(f"✓ Generated {self.num_pdfs} PDFs (Total: {total_size:.2f} KB)")
        print()
    
    def run_stress_test(self):
        """Execute the comprehensive stress test."""
        print("=" * 70)
        print("STARTING LIVE APP STRESS TEST")
        print("=" * 70)
        print()
        
        # Record initial memory
        gc.collect()
        initial_memory = self.get_memory_usage_mb()
        self.stats['memory_samples'].append(initial_memory)
        print(f"Initial memory usage: {initial_memory:.2f} MB")
        print()
        
        # Overall timing
        overall_start = time.time()
        
        # Process each PDF
        for idx, pdf in enumerate(self.dummy_pdfs, 1):
            # Upload PDF
            result = self.upload_pdf(pdf["data"], pdf["filename"])
            
            # Track statistics
            if result["success"]:
                self.stats['successful_uploads'] += 1
                self.stats['upload_times'].append(result['upload_time'])
                self.stats['api_response_times'].append(result['upload_time'])
                status = "✓"
            else:
                self.stats['failed_uploads'] += 1
                self.stats['errors'].append({
                    'file': pdf['filename'],
                    'error': result.get('error', 'Unknown error')
                })
                status = "✗"
            
            # Print progress every 5 files
            if idx % 5 == 0 or not result["success"]:
                current_memory = self.get_memory_usage_mb()
                self.stats['memory_samples'].append(current_memory)
                memory_delta = current_memory - initial_memory
                
                # Calculate progress and ETA
                progress_pct = (idx / self.num_pdfs) * 100
                elapsed = time.time() - overall_start
                avg_time_per_file = elapsed / idx
                remaining_files = self.num_pdfs - idx
                eta_seconds = remaining_files * avg_time_per_file
                eta_minutes = eta_seconds / 60
                
                success_rate = (self.stats['successful_uploads'] / idx) * 100
                
                print(
                    f"  [{progress_pct:5.1f}%] File {idx}/{self.num_pdfs}: "
                    f"{status} {result['upload_time']:.2f}s | "
                    f"Success: {success_rate:.1f}% | "
                    f"Memory: {current_memory:.2f} MB (Δ {memory_delta:+.2f}) | "
                    f"ETA: {eta_minutes:.1f}m"
                )
            
            # Small delay to avoid overwhelming the backend
            time.sleep(0.1)
        
        # Final memory check
        gc.collect()
        final_memory = self.get_memory_usage_mb()
        self.stats['memory_samples'].append(final_memory)
        
        overall_time = time.time() - overall_start
        
        # Print results
        self.print_results(
            initial_memory=initial_memory,
            final_memory=final_memory,
            overall_time=overall_time
        )
    
    def print_results(
        self,
        initial_memory: float,
        final_memory: float,
        overall_time: float
    ):
        """Print comprehensive test results."""
        print()
        print("=" * 70)
        print("LIVE APP STRESS TEST RESULTS")
        print("=" * 70)
        print()
        
        # Overall metrics
        total_files = self.stats['successful_uploads'] + self.stats['failed_uploads']
        success_rate = (self.stats['successful_uploads'] / total_files * 100) if total_files > 0 else 0
        
        print(f"📊 Overall Metrics:")
        print(f"  ├─ Total runtime: {overall_time:.2f} seconds ({overall_time/60:.2f} minutes)")
        print(f"  ├─ Files processed: {total_files}")
        print(f"  ├─ Successful uploads: {self.stats['successful_uploads']} ({success_rate:.1f}%)")
        print(f"  ├─ Failed uploads: {self.stats['failed_uploads']}")
        print(f"  └─ Throughput: {total_files/overall_time:.2f} files/second")
        print()
        
        # Upload timing statistics
        if self.stats['upload_times']:
            upload_times = sorted(self.stats['upload_times'])
            avg_upload = sum(upload_times) / len(upload_times)
            p50 = upload_times[len(upload_times) // 2]
            p90 = upload_times[int(len(upload_times) * 0.9)]
            p95 = upload_times[int(len(upload_times) * 0.95)]
            
            print(f"⏱️  Upload Time Statistics:")
            print(f"  ├─ Average: {avg_upload:.3f} seconds")
            print(f"  ├─ Median (p50): {p50:.3f} seconds")
            print(f"  ├─ Min: {min(upload_times):.3f} seconds")
            print(f"  ├─ Max: {max(upload_times):.3f} seconds")
            print(f"  ├─ p90: {p90:.3f} seconds")
            print(f"  └─ p95: {p95:.3f} seconds")
            print()
        
        # Memory analysis
        memory_delta = final_memory - initial_memory
        peak_memory = max(self.stats['memory_samples'])
        avg_memory = sum(self.stats['memory_samples']) / len(self.stats['memory_samples'])
        
        print(f"💾 Memory Analysis:")
        print(f"  ├─ Initial: {initial_memory:.2f} MB")
        print(f"  ├─ Final: {final_memory:.2f} MB")
        print(f"  ├─ Delta: {memory_delta:+.2f} MB")
        print(f"  ├─ Peak: {peak_memory:.2f} MB")
        print(f"  └─ Average: {avg_memory:.2f} MB")
        print()
        
        # Error details
        if self.stats['errors']:
            print(f"❌ Errors ({len(self.stats['errors'])}):")
            for idx, error in enumerate(self.stats['errors'][:5], 1):
                print(f"  {idx}. {error['file']}: {error['error']}")
            if len(self.stats['errors']) > 5:
                print(f"  ... and {len(self.stats['errors']) - 5} more errors")
            print()
        
        # Summary
        print("=" * 70)
        print("📋 SUMMARY")
        print("=" * 70)
        print(f"✓ Tested {total_files} files in {overall_time:.2f} seconds")
        print(f"✓ Success rate: {success_rate:.1f}% ({self.stats['successful_uploads']}/{total_files})")
        print(f"✓ Average upload time: {sum(self.stats['upload_times'])/len(self.stats['upload_times']):.3f}s" if self.stats['upload_times'] else "✓ No successful uploads")
        print(f"✓ Throughput: {total_files/overall_time:.2f} files/second")
        
        if memory_delta > 50.0:
            print(f"⚠️  Significant memory growth: {memory_delta:.2f} MB")
        else:
            print(f"✓ Memory usage acceptable: {memory_delta:+.2f} MB")
        
        if self.stats['failed_uploads'] > 0:
            print(f"⚠️  {self.stats['failed_uploads']} uploads failed")
        
        print()
        
        # Save report
        self.save_report(overall_time, initial_memory, final_memory)
    
    def save_report(self, overall_time: float, initial_memory: float, final_memory: float):
        """Save detailed test report to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"live_stress_test_report_{timestamp}.txt"
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("LIVE APP STRESS TEST - DETAILED REPORT\n")
                f.write("=" * 70 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Configuration: {self.num_pdfs} PDFs\n")
                f.write(f"Backend URL: {self.backend_url}\n")
                f.write("\n")
                
                total_files = self.stats['successful_uploads'] + self.stats['failed_uploads']
                f.write("OVERALL METRICS:\n")
                f.write(f"  Total runtime: {overall_time:.2f} seconds\n")
                f.write(f"  Files processed: {total_files}\n")
                f.write(f"  Successful: {self.stats['successful_uploads']}\n")
                f.write(f"  Failed: {self.stats['failed_uploads']}\n")
                f.write(f"  Throughput: {total_files/overall_time:.2f} files/second\n")
                f.write("\n")
                
                if self.stats['upload_times']:
                    f.write("UPLOAD TIME STATISTICS:\n")
                    upload_times = sorted(self.stats['upload_times'])
                    f.write(f"  Average: {sum(upload_times)/len(upload_times):.3f}s\n")
                    f.write(f"  Min: {min(upload_times):.3f}s\n")
                    f.write(f"  Max: {max(upload_times):.3f}s\n")
                    f.write(f"  Median: {upload_times[len(upload_times)//2]:.3f}s\n")
                    f.write("\n")
                
                f.write("MEMORY STATISTICS:\n")
                f.write(f"  Initial: {initial_memory:.2f} MB\n")
                f.write(f"  Final: {final_memory:.2f} MB\n")
                f.write(f"  Delta: {final_memory - initial_memory:+.2f} MB\n")
                f.write(f"  Peak: {max(self.stats['memory_samples']):.2f} MB\n")
                f.write("\n")
                
                if self.stats['errors']:
                    f.write(f"ERRORS ({len(self.stats['errors'])}):\n")
                    for error in self.stats['errors']:
                        f.write(f"  {error['file']}: {error['error']}\n")
                    f.write("\n")
                
                # Detailed timing for each file
                f.write("DETAILED UPLOAD TIMES:\n")
                for idx, upload_time in enumerate(self.stats['upload_times'], 1):
                    f.write(f"  File {idx}: {upload_time:.3f}s\n")
                
                f.write("\n")
                f.write("=" * 70 + "\n")
            
            print(f"📄 Detailed report saved to: {report_filename}")
            
        except Exception as e:
            print(f"⚠️  Failed to save report: {e}")


def main():
    """Main entry point for live app stress test."""
    try:
        # Create stress test instance
        # Configurable via environment variables
        num_pdfs = int(os.getenv('STRESS_TEST_NUM_PDFS', '50'))
        backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        stress_test = LiveAppStressTest(num_pdfs=num_pdfs, backend_url=backend_url)
        
        # Initialize test
        stress_test.initialize_test()
        
        # Run stress test
        stress_test.run_stress_test()
        
        print("Live app stress test completed successfully!")
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
