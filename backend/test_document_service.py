"""
Basic tests for DocumentService functionality.
These tests verify the core logic without requiring external dependencies.

Run with: python -m pytest test_document_service.py
Or: python test_document_service.py
"""

import sys
import os

# For standalone execution, add app to path
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services import DocumentService


def test_document_service_initialization():
    """Test that DocumentService can be initialized."""
    print("Testing DocumentService initialization...")
    
    service = DocumentService()
    assert service is not None
    assert service.embedding_model_name == "all-MiniLM-L6-v2"
    
    print("✓ DocumentService initialization test passed")


def test_text_normalization():
    """Test text normalization utilities."""
    print("\nTesting text normalization...")
    
    service = DocumentService()
    
    # Test normalize_text
    text = "Line 1\r\nLine 2\tTabbed\n  Multiple   Spaces  "
    normalized = service._normalize_text(text)
    
    assert "\r\n" not in normalized
    assert "\t" not in normalized
    
    print("✓ Text normalization test passed")


def test_table_detection():
    """Test table detection logic."""
    print("\nTesting table detection...")
    
    service = DocumentService()
    
    # Test various table row formats
    pipe_row = "| Column 1 | Column 2 | Column 3 |"
    tab_row = "Column 1\tColumn 2\tColumn 3"
    space_row = "Column 1     Column 2     Column 3"
    not_table = "This is just normal text"
    
    assert service._looks_like_table_row(pipe_row) == True
    assert service._looks_like_table_row(tab_row) == True
    assert service._looks_like_table_row(space_row) == True
    assert service._looks_like_table_row(not_table) == False
    
    # Test row splitting
    pipe_cols = service._split_row(pipe_row)
    assert len(pipe_cols) == 3
    assert "Column 1" in pipe_cols
    
    print("✓ Table detection test passed")


def test_pattern_matching():
    """Test invoice field detection patterns."""
    print("\nTesting pattern matching...")
    
    service = DocumentService()
    
    # Test date pattern
    test_dates = [
        "2024-12-19",
        "12/19/2024",
        "19.12.2024",
        "2024/12/19"
    ]
    
    for date in test_dates:
        match = service.DATE_PATTERN.search(date)
        assert match is not None, f"Failed to match date: {date}"
    
    # Test amount pattern
    test_amounts = [
        "1000.00",
        "1,000.00",
        "1 000.00",
        "10000,00"
    ]
    
    for amount in test_amounts:
        match = service.AMOUNT_PATTERN.search(amount)
        assert match is not None, f"Failed to match amount: {amount}"
    
    print("✓ Pattern matching test passed")


def test_language_detection():
    """Test language detection."""
    print("\nTesting language detection...")
    
    service = DocumentService()
    
    # Swedish text
    swedish_text = "Faktura nummer 12345. Totalt belopp: 1000 SEK. Förfallodatum: 2024-12-19"
    lang = service._detect_language(swedish_text)
    assert lang == "sv", f"Expected 'sv' but got '{lang}'"
    
    # English text
    english_text = "Invoice number 12345. Total amount: 1000 USD. Due date: 2024-12-19"
    lang = service._detect_language(english_text)
    assert lang == "en", f"Expected 'en' but got '{lang}'"
    
    # Unknown text
    unknown_text = "12345 67890"
    lang = service._detect_language(unknown_text)
    assert lang == "unknown", f"Expected 'unknown' but got '{lang}'"
    
    print("✓ Language detection test passed")


def test_confidence_clamping():
    """Test confidence score clamping."""
    print("\nTesting confidence clamping...")
    
    service = DocumentService()
    
    # Test various values
    assert service._clamp_confidence(0.5) == 0.5
    assert service._clamp_confidence(1.5) == 1.0  # Should be clamped to 1.0
    assert service._clamp_confidence(-0.5) == 0.0  # Should be clamped to 0.0
    assert service._clamp_confidence(0.123456) == 0.12  # Should round to 2 decimals
    
    print("✓ Confidence clamping test passed")


def test_currency_normalization():
    """Test currency normalization."""
    print("\nTesting currency normalization...")
    
    service = DocumentService()
    
    # Test currency tokens
    assert service._find_currency_token("Total: 1000 SEK") == "SEK"
    assert service._find_currency_token("Price: $100") == "$"
    assert service._find_currency_token("Cost: 100€") == "€"
    assert service._find_currency_token("Amount: 1000 kr") == "kr"
    
    # Test normalization
    assert service._normalize_currency("$") == "USD"
    assert service._normalize_currency("€") == "EUR"
    assert service._normalize_currency("kr") == "SEK"
    assert service._normalize_currency("SEK") == "SEK"
    
    print("✓ Currency normalization test passed")


def test_amount_parsing():
    """Test amount parsing and normalization."""
    print("\nTesting amount parsing...")
    
    service = DocumentService()
    
    # Test normalization
    assert service._normalize_amount("1,000.00") == "1000.00"
    assert service._normalize_amount("1 000,00") == "1000.00"
    
    # Test conversion to number
    assert service._amount_to_number("1000.00") == 1000.0
    assert service._amount_to_number("1234.56") == 1234.56
    
    print("✓ Amount parsing test passed")


def test_invoice_field_extraction():
    """Test complete invoice field extraction."""
    print("\nTesting invoice field extraction...")
    
    service = DocumentService()
    
    # Sample invoice text
    invoice_text = """
    INVOICE
    
    Invoice Number: INV-2024-001
    Invoice Date: 2024-12-19
    Due Date: 2025-01-19
    
    Supplier: NordicSecure AB
    Customer: Example Corporation
    
    Subtotal: 8000.00
    VAT (25%): 2000.00
    Total Amount: 10000.00 SEK
    """
    
    key_values, confidences, language = service._build_key_values(invoice_text)
    
    # Check that fields were extracted
    assert key_values['invoice_number'] is not None
    assert key_values['currency'] == "SEK"
    
    # Check confidence scores are valid
    for field, confidence in confidences.items():
        assert 0.0 <= confidence <= 1.0, f"Invalid confidence for {field}: {confidence}"
    
    print("✓ Invoice field extraction test passed")


def run_all_tests():
    """Run all tests."""
    print("="*70)
    print("Running DocumentService Tests")
    print("="*70)
    
    tests = [
        test_document_service_initialization,
        test_text_normalization,
        test_table_detection,
        test_pattern_matching,
        test_language_detection,
        test_confidence_clamping,
        test_currency_normalization,
        test_amount_parsing,
        test_invoice_field_extraction
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {test.__name__}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {test.__name__}")
            print(f"  Error: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
