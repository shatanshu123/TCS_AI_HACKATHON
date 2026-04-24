"""Tests for OCR confidence analyzer."""
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ocr_confidence import OcrConfidenceAnalyzer


class TestOcrConfidenceAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = OcrConfidenceAnalyzer()
    
    def test_get_confidence_level_high(self):
        """Test high confidence level detection."""
        level = self.analyzer._get_confidence_level(90)
        self.assertEqual(level["name"], "high")
        self.assertEqual(level["color"], "#4CAF50")
    
    def test_get_confidence_level_medium(self):
        """Test medium confidence level detection."""
        level = self.analyzer._get_confidence_level(75)
        self.assertEqual(level["name"], "medium")
        self.assertEqual(level["color"], "#FFC107")
    
    def test_get_confidence_level_low(self):
        """Test low confidence level detection."""
        level = self.analyzer._get_confidence_level(50)
        self.assertEqual(level["name"], "low")
        self.assertEqual(level["color"], "#F44336")
    
    def test_analyze_extraction_confidence(self):
        """Test extraction confidence analysis."""
        extraction = {
            "vendor": {
                "value": "ACME Corp",
                "confidence": 0.95,
                "source": "masked_text_openai"
            },
            "invoice_number": {
                "value": "INV-001",
                "confidence": 0.85,
                "source": "masked_text_openai"
            },
            "total_amount": {
                "value": "1000.00",
                "confidence": 0.65,
                "source": "local"
            }
        }
        
        analysis = self.analyzer.analyze_extraction_confidence(extraction)
        
        self.assertIn("fields", analysis)
        self.assertIn("summary", analysis)
        self.assertEqual(len(analysis["fields"]), 3)
        self.assertEqual(analysis["summary"]["total_fields"], 3)
    
    def test_summary_statistics(self):
        """Test summary statistics generation."""
        fields = [
            {"field": "vendor", "confidence": 95, "requires_review": False, "level": {}, "value": "test", "source": "test"},
            {"field": "invoice_number", "confidence": 75, "requires_review": False, "level": {}, "value": "test", "source": "test"},
            {"field": "total_amount", "confidence": 50, "requires_review": True, "level": {}, "value": "test", "source": "test"},
        ]
        
        summary = self.analyzer._generate_summary(fields)
        
        self.assertEqual(summary["total_fields"], 3)
        self.assertEqual(summary["high_confidence"], 1)
        self.assertEqual(summary["medium_confidence"], 1)
        self.assertEqual(summary["low_confidence"], 1)
        self.assertTrue(summary["review_required"])
    
    def test_status_determination(self):
        """Test status determination based on confidence."""
        # All high confidence
        status = self.analyzer._get_status(3, 0, 0, 3)
        self.assertEqual(status, "ready")
        
        # Has low confidence
        status = self.analyzer._get_status(2, 0, 1, 3)
        self.assertEqual(status, "needs_review")
        
        # Has medium confidence
        status = self.analyzer._get_status(1, 2, 0, 3)
        self.assertEqual(status, "review_recommended")
    
    def test_generate_html_report(self):
        """Test HTML report generation."""
        extraction = {
            "vendor": {
                "value": "ACME Corp",
                "confidence": 0.95,
                "source": "test"
            },
            "invoice_number": {
                "value": "INV-001",
                "confidence": 0.50,
                "source": "test"
            }
        }
        
        html = self.analyzer.generate_html_report(extraction)
        
        self.assertIn("<table", html)
        self.assertIn("vendor", html)
        self.assertIn("invoice_number", html)
        self.assertIn("95%", html)
        self.assertIn("50%", html)
        self.assertIn("⚠️ Review", html)


if __name__ == "__main__":
    unittest.main()
