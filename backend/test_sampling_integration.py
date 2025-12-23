"""
Integration test for sampling strategy with PDF parsing
"""
import unittest
import io
from unittest.mock import MagicMock, patch
from backend.app.services.document_service import DocumentService


class TestSamplingStrategyIntegration(unittest.TestCase):
    """Test sampling strategy with mock PDF parsing"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = DocumentService()
    
    @patch('backend.app.services.document_service.PyPDF2')
    def test_parse_pdf_with_linear_strategy(self, mock_pypdf2):
        """Test parsing PDF with linear strategy"""
        # Mock PDF with 10 pages
        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [MagicMock() for _ in range(10)]
        
        # Configure each page to return text with enough content to not trigger OCR
        for i, page in enumerate(mock_reader.pages):
            page.extract_text.return_value = f"Page {i+1} content with sufficient text to avoid OCR detection. " * 10
        
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        # Parse with linear strategy, max 5 pages
        result = self.service.parse_pdf(
            b"fake_pdf_bytes",
            filename="test.pdf",
            max_pages=5,
            sampling_strategy="linear"
        )
        
        # Should extract first 5 pages
        self.assertEqual(len(result["pages"]), 5)
        self.assertEqual(result["pages"][0]["page_number"], 1)
        self.assertEqual(result["pages"][4]["page_number"], 5)
        
        # Verify only first 5 pages were accessed
        for i in range(5):
            mock_reader.pages[i].extract_text.assert_called_once()
        for i in range(5, 10):
            mock_reader.pages[i].extract_text.assert_not_called()
    
    @patch('backend.app.services.document_service.PyPDF2')
    def test_parse_pdf_with_random_strategy(self, mock_pypdf2):
        """Test parsing PDF with random strategy"""
        # Mock PDF with 10 pages
        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [MagicMock() for _ in range(10)]
        
        # Configure each page to return text with enough content to not trigger OCR
        for i, page in enumerate(mock_reader.pages):
            page.extract_text.return_value = f"Page {i+1} content with sufficient text to avoid OCR detection. " * 10
        
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        # Parse with random strategy
        result = self.service.parse_pdf(
            b"fake_pdf_bytes",
            filename="test.pdf",
            max_pages=5,
            sampling_strategy="random"
        )
        
        # Should extract 3 pages (start, middle, end)
        self.assertEqual(len(result["pages"]), 3)
        
        # Verify pages are from start (1), middle (5), and end (10)
        page_numbers = [page["page_number"] for page in result["pages"]]
        self.assertEqual(page_numbers, [1, 5, 10])  # 0-indexed: 0, 4, 9 -> 1-indexed: 1, 5, 10
        
        # Verify only selected pages were accessed
        mock_reader.pages[0].extract_text.assert_called_once()
        mock_reader.pages[4].extract_text.assert_called_once()
        mock_reader.pages[9].extract_text.assert_called_once()
    
    @patch('backend.app.services.document_service.PyPDF2')
    def test_parse_pdf_with_random_strategy_small_doc(self, mock_pypdf2):
        """Test parsing small PDF with random strategy"""
        # Mock PDF with only 2 pages
        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [MagicMock() for _ in range(2)]
        
        # Configure each page to return text with enough content to not trigger OCR
        for i, page in enumerate(mock_reader.pages):
            page.extract_text.return_value = f"Page {i+1} content with sufficient text to avoid OCR detection. " * 10
        
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        # Parse with random strategy
        result = self.service.parse_pdf(
            b"fake_pdf_bytes",
            filename="test.pdf",
            max_pages=5,
            sampling_strategy="random"
        )
        
        # Should extract both pages
        self.assertEqual(len(result["pages"]), 2)
        self.assertEqual(result["pages"][0]["page_number"], 1)
        self.assertEqual(result["pages"][1]["page_number"], 2)
    
    @patch('backend.app.services.document_service.PyPDF2')
    def test_parse_pdf_default_strategy(self, mock_pypdf2):
        """Test parsing PDF with default strategy (linear)"""
        # Mock PDF with 5 pages
        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [MagicMock() for _ in range(5)]
        
        # Configure each page to return text with enough content to not trigger OCR
        for i, page in enumerate(mock_reader.pages):
            page.extract_text.return_value = f"Page {i+1} content with sufficient text to avoid OCR detection. " * 10
        
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        # Parse without specifying strategy (should default to linear)
        result = self.service.parse_pdf(
            b"fake_pdf_bytes",
            filename="test.pdf",
            max_pages=3
        )
        
        # Should extract first 3 pages (linear default)
        self.assertEqual(len(result["pages"]), 3)
        self.assertEqual(result["pages"][0]["page_number"], 1)
        self.assertEqual(result["pages"][1]["page_number"], 2)
        self.assertEqual(result["pages"][2]["page_number"], 3)


if __name__ == '__main__':
    unittest.main()
