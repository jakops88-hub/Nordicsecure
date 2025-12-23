#!/usr/bin/env python3
"""
Example script demonstrating GPU acceleration and PDF renaming features.

This script shows how to:
1. Detect available GPU hardware
2. Use the RenameService to rename PDFs based on content
3. Process multilingual documents

Note: Requires Ollama to be running with Llama 3 model.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.utils.hardware_detector import get_hardware_detector


def demo_hardware_detection():
    """Demonstrate hardware detection."""
    print("=" * 60)
    print("GPU Hardware Detection Demo")
    print("=" * 60)
    
    detector = get_hardware_detector()
    hardware = detector.detect_hardware()
    
    print(f"\n✓ Hardware Detection Complete:")
    print(f"  Device: {hardware['device']}")
    print(f"  Device Name: {hardware['device_name']}")
    print(f"  CUDA Available: {hardware['cuda_available']}")
    print(f"  MPS Available: {hardware['mps_available']}")
    print(f"  GPU Layers: {hardware['gpu_layers']}")
    print(f"  Backend: {hardware['backend']}")
    
    if hardware['device'] != 'cpu':
        print(f"\n🚀 GPU acceleration is ENABLED!")
        print(f"   Expected speedup: 5-10x faster inference")
    else:
        print(f"\n⚠️  GPU acceleration is NOT available")
        print(f"   Consider installing PyTorch with CUDA support for better performance")
    
    print()


def demo_rename_service():
    """Demonstrate PDF renaming service (mock without actual LLM call)."""
    print("=" * 60)
    print("PDF Renaming Service Demo")
    print("=" * 60)
    
    from backend.app.services.rename_service import RenameService
    
    # Create service instance (without document_service for demo)
    service = RenameService(document_service=None)
    
    print("\n✓ RenameService initialized")
    print(f"  Ollama URL: {service.ollama_base_url}")
    print(f"  Model: {service.model_name}")
    
    # Test filename sanitization
    print("\n✓ Testing filename sanitization:")
    
    test_cases = [
        ("Rich Dad Poor Dad", "Finance Guide"),
        ("J.K. Rowling", "Harry Potter and the Philosopher's Stone"),
        ("ਅਮਰੀਕ ਸਿੰਘ", "ਪੰਜਾਬ ਦੀ ਇਤਿਹਾਸ"),
        ("中文作者", "书名"),
        ("مؤلف", "عنوان الكتاب"),
    ]
    
    for author, title in test_cases:
        filename = service.generate_new_filename(author, title)
        print(f"  Author: {author}")
        print(f"  Title: {title}")
        print(f"  → Filename: {filename}")
        print()
    
    print("✓ UTF-8 filenames are fully supported!")


def demo_api_usage():
    """Show example API usage."""
    print("=" * 60)
    print("API Usage Examples")
    print("=" * 60)
    
    print("\n1. Rename a single PDF:")
    print("""
curl -X POST http://localhost:8000/rename/single \\
  -H "Content-Type: application/json" \\
  -d '{
    "file_path": "/path/to/rich dad poor dad.pdf",
    "max_pages": 3
  }'
""")
    
    print("\n2. Batch rename entire folder:")
    print("""
curl -X POST http://localhost:8000/rename/batch \\
  -H "Content-Type: application/json" \\
  -d '{
    "folder_path": "/path/to/books",
    "max_pages": 3
  }'
""")
    
    print("\n3. Expected response (single file):")
    print("""
{
  "original_name": "rich dad poor dad.pdf",
  "new_name": "Robert Kiyosaki - Rich Dad Poor Dad.pdf",
  "success": true,
  "author": "Robert Kiyosaki",
  "title": "Rich Dad Poor Dad",
  "confidence": 0.92,
  "error": null
}
""")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("NordicSecure - GPU Acceleration & PDF Renaming Demo")
    print("=" * 60)
    print()
    
    try:
        # Demo 1: Hardware detection
        demo_hardware_detection()
        
        # Demo 2: Rename service
        demo_rename_service()
        
        # Demo 3: API usage examples
        demo_api_usage()
        
        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Ensure Ollama is running: ollama serve")
        print("2. Pull Llama 3 model: ollama pull llama3")
        print("3. Start the API: cd backend && python main.py")
        print("4. Try renaming a PDF using the API endpoints above")
        print("\nFor full documentation, see: GPU_AND_MULTILINGUAL_GUIDE.md")
        print()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
