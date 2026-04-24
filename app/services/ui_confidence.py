"""UI-level confidence visualization combining OCR and field extraction confidence."""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class FieldConfidence:
    """Represents confidence data for a single extracted field."""
    field: str
    value: Optional[str]
    confidence: float  # 0-1 from extraction
    source: str  # "masked_text_openai", "masked_text_genailab", "local", "reviewer"
    tokens: List[Dict[str, Any]]  # OCR tokens that contribute to this field
    avg_ocr_confidence: float  # Average confidence of contributing OCR tokens
    
    def is_low_confidence(self, threshold: float = 0.7) -> bool:
        """Check if field confidence is below threshold."""
        return self.confidence < threshold
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "value": self.value,
            "extraction_confidence": self.confidence,
            "source": self.source,
            "ocr_tokens_count": len(self.tokens),
            "avg_ocr_confidence": round(self.avg_ocr_confidence, 2),
            "overall_confidence": self._compute_overall_confidence(),
            "recommendation": self._get_recommendation(),
        }
    
    def _compute_overall_confidence(self) -> float:
        """Compute weighted overall confidence from extraction and OCR."""
        # Weight: 60% extraction confidence, 40% average OCR confidence
        extraction_weight = 0.6
        ocr_weight = 0.4
        overall = (self.confidence * extraction_weight) + (self.avg_ocr_confidence / 100.0 * ocr_weight)
        return round(overall, 2)
    
    def _get_recommendation(self) -> str:
        """Get recommendation based on overall confidence."""
        overall = self._compute_overall_confidence()
        if overall >= 0.85:
            return "auto_accept"
        elif overall >= 0.70:
            return "review"
        else:
            return "manual_entry"


class UiConfidenceVisualization:
    """Generates UI-friendly confidence visualization combining OCR and extraction data."""
    
    def __init__(self):
        self.ocr_confidence_threshold = 70.0  # percentage
        self.extraction_confidence_threshold = 0.7  # normalized
    
    def generate_field_confidence_view(
        self,
        extraction: Dict[str, Any],
        ocr_tokens: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate UI view combining extraction and OCR confidence."""
        
        field_confidences = []
        extraction_fields = [
            "vendor", "invoice_number", "invoice_date", "due_date",
            "currency", "total_amount", "tax_id_token"
        ]
        
        for field in extraction_fields:
            field_data = extraction.get(field, {})
            if isinstance(field_data, dict):
                value = field_data.get("value")
                conf = field_data.get("confidence", 0.5)
                source = field_data.get("source", "unknown")
            else:
                value = field_data
                conf = 0.5
                source = "unknown"
            
            # Find OCR tokens that might contribute to this field
            contributing_tokens = self._find_contributing_tokens(value, ocr_tokens)
            avg_ocr_conf = (
                sum(t.get("confidence", 0) for t in contributing_tokens) / len(contributing_tokens)
                if contributing_tokens else 0
            )
            
            field_conf = FieldConfidence(
                field=field,
                value=value,
                confidence=conf,
                source=source,
                tokens=contributing_tokens,
                avg_ocr_confidence=avg_ocr_conf,
            )
            field_confidences.append(field_conf)
        
        return {
            "fields": [f.to_dict() for f in field_confidences],
            "summary": self._generate_summary(field_confidences),
            "health": self._assess_extraction_health(field_confidences),
        }
    
    def _find_contributing_tokens(
        self,
        field_value: Optional[str],
        ocr_tokens: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Find OCR tokens that might contribute to a field value."""
        if not field_value:
            return []
        
        # Simple heuristic: find tokens that match parts of the field value
        contributing = []
        field_lower = str(field_value).lower()
        field_parts = field_lower.split()
        
        for token in ocr_tokens:
            token_text = token.get("text", "").lower()
            if token_text in field_parts or any(part in token_text for part in field_parts):
                contributing.append(token)
        
        return contributing
    
    def _generate_summary(self, field_confidences: List[FieldConfidence]) -> Dict[str, Any]:
        """Generate overall summary statistics."""
        if not field_confidences:
            return {}
        
        total_fields = len(field_confidences)
        high_conf_count = sum(1 for f in field_confidences if not f.is_low_confidence())
        low_conf_count = total_fields - high_conf_count
        
        avg_extraction_conf = sum(f.confidence for f in field_confidences) / total_fields
        avg_ocr_conf = sum(f.avg_ocr_confidence for f in field_confidences) / total_fields
        
        return {
            "total_fields": total_fields,
            "high_confidence_fields": high_conf_count,
            "low_confidence_fields": low_conf_count,
            "avg_extraction_confidence": round(avg_extraction_conf, 2),
            "avg_ocr_confidence": round(avg_ocr_conf, 2),
            "extraction_quality": self._assess_quality(high_conf_count, total_fields),
        }
    
    def _assess_extraction_health(self, field_confidences: List[FieldConfidence]) -> Dict[str, Any]:
        """Assess overall extraction quality and provide recommendations."""
        recommendations = {
            "auto_accept": [],
            "review": [],
            "manual_entry": [],
        }
        
        for fc in field_confidences:
            rec = fc._get_recommendation()
            recommendations[rec].append(fc.field)
        
        return {
            "status": self._get_health_status(recommendations),
            "recommendations": recommendations,
            "next_action": self._get_next_action(recommendations),
        }
    
    def _assess_quality(self, high_conf_count: int, total: int) -> str:
        """Assess extraction quality level."""
        if total == 0:
            return "unknown"
        ratio = high_conf_count / total
        if ratio >= 0.85:
            return "excellent"
        elif ratio >= 0.70:
            return "good"
        elif ratio >= 0.50:
            return "fair"
        else:
            return "poor"
    
    def _get_health_status(self, recommendations: Dict[str, List[str]]) -> str:
        """Get overall health status."""
        if recommendations["manual_entry"]:
            return "needs_review"
        elif recommendations["review"]:
            return "review_recommended"
        else:
            return "ready_to_process"
    
    def _get_next_action(self, recommendations: Dict[str, List[str]]) -> str:
        """Get recommended next action."""
        if recommendations["manual_entry"]:
            return f"Manually enter: {', '.join(recommendations['manual_entry'])}"
        elif recommendations["review"]:
            return f"Review these fields: {', '.join(recommendations['review'])}"
        else:
            return "Invoice extraction looks good, ready for processing"
    
    def generate_ui_widget_data(
        self,
        invoice_id: str,
        extraction: Dict[str, Any],
        ocr_tokens: List[Dict[str, Any]],
        original_filename: str = "",
    ) -> Dict[str, Any]:
        """Generate complete UI widget data for display."""
        confidence_view = self.generate_field_confidence_view(extraction, ocr_tokens)
        
        return {
            "invoice_id": invoice_id,
            "original_filename": original_filename,
            "widget_data": {
                "fields": confidence_view["fields"],
                "summary": confidence_view["summary"],
                "health": confidence_view["health"],
                "ui_hints": {
                    "color_scheme": self._get_color_scheme(),
                    "show_ocr_tokens": True,
                    "enable_manual_override": True,
                    "show_confidence_percentages": True,
                }
            }
        }
    
    def _get_color_scheme(self) -> Dict[str, str]:
        """Get color scheme for UI rendering."""
        return {
            "auto_accept": "#4CAF50",      # green
            "review": "#FFC107",            # amber
            "manual_entry": "#F44336",      # red
            "high_confidence": "#ccffcc",   # light green
            "medium_confidence": "#ffffcc", # light yellow
            "low_confidence": "#ffcccc",    # light red
        }
