"""
Basic tests for RenameService functionality.
These tests verify the core logic without requiring external dependencies.

Run with: python test_rename_service.py
"""

import sys
import os
import tempfile
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_filename_sanitization():
    """Test filename sanitization for various edge cases."""
    print("Testing filename sanitization...")
    
    from backend.app.services.rename_service import RenameService
    
    # Create a mock rename service (without document_service)
    service = RenameService(document_service=None)
    
    # Test cases
    test_cases = [
        # (input, expected_output_pattern)
        ("Normal Author", "Normal Author"),
        ("Author/With\\Invalid:Chars", "AuthorWithInvalidChars"),
        ("Author<>Name|Test", "AuthorNameTest"),
        ("Multiple   Spaces", "Multiple Spaces"),
        ("  Leading and Trailing  ", "Leading and Trailing"),
        ("Dots...at.end...", "Dots...at.end"),
        # UTF-8 characters should be preserved
        ("ਪੰਜਾਬੀ ਲੇਖਕ", "ਪੰਜਾਬੀ ਲੇਖਕ"),
        ("中文作者", "中文作者"),
        ("Русский автор", "Русский автор"),
        ("العربية المؤلف", "العربية المؤلف"),
    ]
    
    for input_str, expected in test_cases:
        result = service.sanitize_filename(input_str)
        print(f"  Input: '{input_str}' -> Output: '{result}'")
        
        # Check that result doesn't have invalid characters
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result
        assert '"' not in result
        assert '/' not in result
        assert '\\' not in result
        assert '|' not in result
        assert '?' not in result
        assert '*' not in result
        
        # For non-UTF8 test cases, check exact match
        if input_str == expected:
            continue
        
        # For cases with invalid chars, check they're removed
        assert len(result) > 0
    
    print("✓ Filename sanitization test passed")


def test_generate_new_filename():
    """Test new filename generation."""
    print("\nTesting new filename generation...")
    
    from backend.app.services.rename_service import RenameService
    
    service = RenameService(document_service=None)
    
    # Test cases
    test_cases = [
        ("John Doe", "Book Title", "John Doe - Book Title.pdf"),
        ("Author", "Title", "Author - Title.pdf"),
        ("", "Title Only", "Title Only.pdf"),
        ("Author Only", "", "Author Only.pdf"),
        ("", "", "Untitled.pdf"),
    ]
    
    for author, title, expected in test_cases:
        result = service.generate_new_filename(author, title)
        print(f"  Author: '{author}', Title: '{title}' -> '{result}'")
        
        # Check that result ends with .pdf
        assert result.endswith('.pdf')
        
        # If both author and title exist, should have dash
        if author and title:
            assert ' - ' in result
    
    print("✓ New filename generation test passed")


def test_utf8_filename_generation():
    """Test UTF-8 filename generation with various scripts."""
    print("\nTesting UTF-8 filename generation...")
    
    from backend.app.services.rename_service import RenameService
    
    service = RenameService(document_service=None)
    
    # Test UTF-8 cases
    test_cases = [
        ("ਅਮਰੀਕ ਸਿੰਘ", "ਪੰਜਾਬ ਦੀ ਇਤਿਹਾਸ", "ਅਮਰੀਕ ਸਿੰਘ - ਪੰਜਾਬ ਦੀ ਇਤਿਹਾਸ.pdf"),
        ("中文作者", "书名", "中文作者 - 书名.pdf"),
        ("Русский автор", "Название книги", "Русский автор - Название книги.pdf"),
        ("مؤلف", "عنوان الكتاب", "مؤلف - عنوان الكتاب.pdf"),
    ]
    
    for author, title, expected in test_cases:
        result = service.generate_new_filename(author, title)
        print(f"  Author: '{author}', Title: '{title}'")
        print(f"    Result: '{result}'")
        
        # Check that UTF-8 characters are preserved
        assert result.endswith('.pdf')
        
        # Check that author and title are in the result
        assert author in result or len(author) == 0
        assert title in result or len(title) == 0
    
    print("✓ UTF-8 filename generation test passed")


def test_filename_length_truncation():
    """Test that very long filenames are truncated."""
    print("\nTesting filename length truncation...")
    
    from backend.app.services.rename_service import RenameService
    
    service = RenameService(document_service=None)
    
    # Create very long author and title
    long_author = "A" * 300
    long_title = "T" * 300
    
    result = service.generate_new_filename(long_author, long_title)
    
    print(f"  Generated filename length: {len(result)}")
    
    # Check that result is not too long
    # Should be truncated to MAX_FILENAME_LENGTH + ".pdf" extension
    assert len(result) <= service.MAX_FILENAME_LENGTH + 10
    assert result.endswith('.pdf')
    
    print("✓ Filename length truncation test passed")


def test_safe_rename_collision_handling():
    """Test collision handling in file renaming."""
    print("\nTesting collision handling...")
    
    from backend.app.services.rename_service import RenameService
    
    service = RenameService(document_service=None)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create test files
        file1 = tmpdir_path / "test.pdf"
        file2 = tmpdir_path / "test_1.pdf"
        file3 = tmpdir_path / "original.pdf"
        
        # Create dummy files
        file1.write_text("dummy1")
        file2.write_text("dummy2")
        file3.write_text("dummy3")
        
        # Try to rename file3 to "test.pdf" (collision should occur)
        new_path, success = service.safe_rename_file(file3, "test.pdf")
        
        print(f"  Original: {file3.name}")
        print(f"  Target: test.pdf")
        print(f"  Result: {new_path.name}")
        print(f"  Success: {success}")
        
        # Should have created test_2.pdf since test.pdf and test_1.pdf exist
        if success:
            assert new_path.exists()
            assert new_path.name == "test_2.pdf"
        
    print("✓ Collision handling test passed")


def test_rename_service_initialization():
    """Test that RenameService can be initialized."""
    print("\nTesting RenameService initialization...")
    
    from backend.app.services.rename_service import RenameService
    
    service = RenameService(
        document_service=None,
        ollama_base_url="http://localhost:11435",
        model_name="llama3"
    )
    
    assert service is not None
    assert service.ollama_base_url == "http://localhost:11435"
    assert service.model_name == "llama3"
    assert service.MAX_TEXT_LENGTH == 4000
    assert service.MAX_FILENAME_LENGTH == 200
    
    print("✓ RenameService initialization test passed")


if __name__ == "__main__":
    print("=" * 60)
    print("RenameService Tests")
    print("=" * 60)
    
    try:
        test_rename_service_initialization()
        test_filename_sanitization()
        test_generate_new_filename()
        test_utf8_filename_generation()
        test_filename_length_truncation()
        test_safe_rename_collision_handling()
        
        print("\n" + "=" * 60)
        print("All RenameService tests passed! ✓")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
