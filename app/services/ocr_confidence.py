"""OCR confidence analyzer - simplified efficient version."""
from typing import List, Dict, Any


class OcrConfidenceAnalyzer:
    """Lightweight OCR confidence analyzer and visualizer."""
    
    CONFIDENCE_LEVELS = {
        "high": {"min": 85, "color": "#4CAF50", "label": "High"},
        "medium": {"min": 70, "color": "#FFC107", "label": "Medium"},
        "low": {"min": 0, "color": "#F44336", "label": "Low"},
    }
    
    def analyze_extraction_confidence(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze confidence of extracted invoice fields."""
        fields_analysis = []
        
        for field_name, field_data in extraction.items():
            if not isinstance(field_data, dict):
                continue
            
            confidence = field_data.get("confidence", 0.5)
            value = field_data.get("value")
            source = field_data.get("source", "unknown")
            
            # Normalize to 0-100 scale if needed
            conf_percent = int(confidence * 100) if confidence <= 1 else int(confidence)
            
            level = self._get_confidence_level(conf_percent)
            
            fields_analysis.append({
                "field": field_name,
                "value": value,
                "confidence": conf_percent,
                "level": level,
                "source": source,
                "requires_review": conf_percent < 70,
            })
        
        return {
            "fields": fields_analysis,
            "summary": self._generate_summary(fields_analysis),
        }
    
    def _get_confidence_level(self, confidence: int) -> Dict[str, Any]:
        """Get confidence level info."""
        for level_name, level_info in self.CONFIDENCE_LEVELS.items():
            if confidence >= level_info["min"]:
                return {
                    "name": level_name,
                    "label": level_info["label"],
                    "color": level_info["color"],
                }
        return self.CONFIDENCE_LEVELS["low"]
    
    def _generate_summary(self, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not fields:
            return {}
        
        total = len(fields)
        high_conf = sum(1 for f in fields if f["confidence"] >= 85)
        medium_conf = sum(1 for f in fields if 70 <= f["confidence"] < 85)
        low_conf = sum(1 for f in fields if f["confidence"] < 70)
        
        avg_conf = sum(f["confidence"] for f in fields) / total if total else 0
        
        return {
            "total_fields": total,
            "high_confidence": high_conf,
            "medium_confidence": medium_conf,
            "low_confidence": low_conf,
            "average_confidence": int(avg_conf),
            "status": self._get_status(high_conf, medium_conf, low_conf, total),
            "review_required": low_conf > 0,
        }
    
    def _get_status(self, high: int, medium: int, low: int, total: int) -> str:
        """Determine overall extraction status."""
        if low > 0:
            return "needs_review"
        elif medium > total * 0.3:
            return "review_recommended"
        else:
            return "ready"
    
    def generate_html_report(self, extraction: Dict[str, Any]) -> str:
        """Generate simple HTML report."""
        analysis = self.analyze_extraction_confidence(extraction)
        
        html = [
            '<div style="font-family: Arial, sans-serif; padding: 20px;">',
            '<h3>Extraction Confidence Report</h3>',
            '<table style="width:100%; border-collapse: collapse;">',
            '<tr style="background-color: #f0f0f0;">',
            '<th style="border: 1px solid #ddd; padding: 10px; text-align: left;">Field</th>',
            '<th style="border: 1px solid #ddd; padding: 10px; text-align: center;">Confidence</th>',
            '<th style="border: 1px solid #ddd; padding: 10px; text-align: left;">Status</th>',
            '</tr>',
        ]
        
        for field in analysis["fields"]:
            conf = field["confidence"]
            level = field["level"]
            value_preview = (field["value"] or "")[:30]
            
            html.append('<tr>')
            html.append(f'<td style="border: 1px solid #ddd; padding: 10px;">{field["field"]}</td>')
            html.append(
                f'<td style="border: 1px solid #ddd; padding: 10px; text-align: center; '
                f'background-color: {level["color"]}20; color: {level["color"]}; font-weight: bold;">'
                f'{conf}%</td>'
            )
            review = "⚠️ Review" if field["requires_review"] else "✓ OK"
            html.append(f'<td style="border: 1px solid #ddd; padding: 10px;">{review}</td>')
            html.append('</tr>')
        
        html.extend([
            '</table>',
            f'<p><strong>Summary:</strong> {analysis["summary"]["high_confidence"]}/{analysis["summary"]["total_fields"]} fields have high confidence.</p>',
            '</div>',
        ])
        
        return "".join(html)

