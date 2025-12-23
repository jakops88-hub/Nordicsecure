"""
Test sampling strategy functionality in DocumentService
"""
import unittest
from backend.app.services.document_service import DocumentService


class TestSamplingStrategy(unittest.TestCase):
    """Test sampling strategy page selection logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = DocumentService()
    
    def test_linear_strategy_with_max_pages(self):
        """Test linear strategy selects first N pages"""
        # Test with 10 total pages, max 5 pages
        indices = self.service._get_page_indices_to_extract(10, 5, "linear")
        self.assertEqual(indices, [0, 1, 2, 3, 4])
    
    def test_linear_strategy_no_max_pages(self):
        """Test linear strategy with no max_pages returns all pages"""
        # Test with 5 total pages, no limit
        indices = self.service._get_page_indices_to_extract(5, None, "linear")
        self.assertEqual(indices, [0, 1, 2, 3, 4])
    
    def test_linear_strategy_more_max_than_total(self):
        """Test linear strategy when max_pages > total_pages"""
        # Test with 3 total pages, max 5 pages
        indices = self.service._get_page_indices_to_extract(3, 5, "linear")
        self.assertEqual(indices, [0, 1, 2])
    
    def test_random_strategy_picks_start_middle_end(self):
        """Test random strategy picks pages from start, middle, and end"""
        # Test with 10 total pages
        indices = self.service._get_page_indices_to_extract(10, 5, "random")
        # Should pick page 0 (start), 4 (middle), and 9 (end)
        self.assertEqual(len(indices), 3)
        self.assertIn(0, indices)  # First page
        self.assertIn(4, indices)  # Middle page ((10-1) // 2)
        self.assertIn(9, indices)  # Last page
        # Should be sorted
        self.assertEqual(indices, sorted(indices))
    
    def test_random_strategy_single_page(self):
        """Test random strategy with single page"""
        indices = self.service._get_page_indices_to_extract(1, 5, "random")
        self.assertEqual(indices, [0])
    
    def test_random_strategy_two_pages(self):
        """Test random strategy with two pages"""
        indices = self.service._get_page_indices_to_extract(2, 5, "random")
        self.assertEqual(indices, [0, 1])
    
    def test_random_strategy_three_pages(self):
        """Test random strategy with exactly three pages"""
        indices = self.service._get_page_indices_to_extract(3, 5, "random")
        self.assertEqual(indices, [0, 1, 2])
    
    def test_random_strategy_large_document(self):
        """Test random strategy with large document"""
        # Test with 100 pages
        indices = self.service._get_page_indices_to_extract(100, 5, "random")
        self.assertEqual(len(indices), 3)
        self.assertIn(0, indices)      # First page
        self.assertIn(49, indices)     # Middle page ((100-1) // 2)
        self.assertIn(99, indices)     # Last page
    
    def test_random_strategy_respects_max_pages_1(self):
        """Test random strategy respects max_pages=1"""
        indices = self.service._get_page_indices_to_extract(10, 1, "random")
        self.assertEqual(indices, [0])
    
    def test_random_strategy_respects_max_pages_2(self):
        """Test random strategy respects max_pages=2"""
        indices = self.service._get_page_indices_to_extract(10, 2, "random")
        self.assertEqual(len(indices), 2)
        self.assertIn(0, indices)  # First page
        self.assertIn(4, indices)  # Middle page
    
    def test_default_strategy_is_linear(self):
        """Test that default/unknown strategy falls back to linear"""
        indices = self.service._get_page_indices_to_extract(10, 5, "unknown")
        self.assertEqual(indices, [0, 1, 2, 3, 4])
    
    def test_case_insensitive_strategy(self):
        """Test that strategy is case-insensitive"""
        indices_lower = self.service._get_page_indices_to_extract(10, 5, "random")
        indices_upper = self.service._get_page_indices_to_extract(10, 5, "RANDOM")
        self.assertEqual(indices_lower, indices_upper)


if __name__ == '__main__':
    unittest.main()
