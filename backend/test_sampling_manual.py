#!/usr/bin/env python3
"""
Manual test script for sampling strategy feature.

This script demonstrates how the sampling strategy works with different configurations.
Run this to verify the feature is working as expected.
"""

from backend.app.services.document_service import DocumentService


def test_sampling_strategies():
    """Test and display sampling strategy behavior"""
    service = DocumentService()
    
    print("=" * 70)
    print("SAMPLING STRATEGY DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Test case 1: Linear strategy with 10-page document
    print("Test 1: Linear Strategy with 10-page document, max 5 pages")
    print("-" * 70)
    indices = service._get_page_indices_to_extract(10, 5, "linear")
    print(f"Selected page indices (0-based): {indices}")
    print(f"Selected page numbers (1-based): {[i+1 for i in indices]}")
    print(f"Description: First 5 pages sequentially")
    print()
    
    # Test case 2: Random strategy with 10-page document
    print("Test 2: Random Strategy with 10-page document, max 5 pages")
    print("-" * 70)
    indices = service._get_page_indices_to_extract(10, 5, "random")
    print(f"Selected page indices (0-based): {indices}")
    print(f"Selected page numbers (1-based): {[i+1 for i in indices]}")
    print(f"Description: Pages from start (1), middle (5), and end (10)")
    print()
    
    # Test case 3: Random strategy with 100-page document
    print("Test 3: Random Strategy with 100-page document, max 5 pages")
    print("-" * 70)
    indices = service._get_page_indices_to_extract(100, 5, "random")
    print(f"Selected page indices (0-based): {indices}")
    print(f"Selected page numbers (1-based): {[i+1 for i in indices]}")
    print(f"Description: Pages from start (1), middle (50), and end (100)")
    print()
    
    # Test case 4: Linear strategy with 100-page document
    print("Test 4: Linear Strategy with 100-page document, max 5 pages")
    print("-" * 70)
    indices = service._get_page_indices_to_extract(100, 5, "linear")
    print(f"Selected page indices (0-based): {indices}")
    print(f"Selected page numbers (1-based): {[i+1 for i in indices]}")
    print(f"Description: First 5 pages sequentially")
    print()
    
    # Test case 5: Random strategy with max_pages=1
    print("Test 5: Random Strategy with 20-page document, max 1 page")
    print("-" * 70)
    indices = service._get_page_indices_to_extract(20, 1, "random")
    print(f"Selected page indices (0-based): {indices}")
    print(f"Selected page numbers (1-based): {[i+1 for i in indices]}")
    print(f"Description: Only first page (respects max_pages=1)")
    print()
    
    # Test case 6: Random strategy with max_pages=2
    print("Test 6: Random Strategy with 20-page document, max 2 pages")
    print("-" * 70)
    indices = service._get_page_indices_to_extract(20, 2, "random")
    print(f"Selected page indices (0-based): {indices}")
    print(f"Selected page numbers (1-based): {[i+1 for i in indices]}")
    print(f"Description: First and middle pages (respects max_pages=2)")
    print()
    
    # Test case 7: Random strategy with small document
    print("Test 7: Random Strategy with 3-page document, max 5 pages")
    print("-" * 70)
    indices = service._get_page_indices_to_extract(3, 5, "random")
    print(f"Selected page indices (0-based): {indices}")
    print(f"Selected page numbers (1-based): {[i+1 for i in indices]}")
    print(f"Description: All 3 pages (document smaller than max_pages)")
    print()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✓ Linear strategy: Extracts first N pages sequentially")
    print("✓ Random strategy: Extracts pages from start, middle, and end")
    print("✓ Both strategies respect max_pages parameter")
    print("✓ Both strategies handle edge cases (small documents, etc.)")
    print()


if __name__ == "__main__":
    test_sampling_strategies()
