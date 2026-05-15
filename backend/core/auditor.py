from typing import Dict, Any, List

def build_audit_trail(regex_result: Dict[str, Any], scored_kpis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Builds the source-level audit trail for extracted KPIs, mapping the verified value 
    to the exact page and line in the original PDF.
    
    Inputs:
    - regex_result: Dict from regex_pipeline.py containing page, line, raw_match
    - scored_kpis: Dict from confidence_scorer.py containing value, confidence, source
    
    Returns:
    - List[Dict]: A list of audit entries mapping each KPI to its source documentation.
    """
    audit_trail = []
    
    for kpi, score_data in scored_kpis.items():
        # Retrieve trace data from regex if it exists
        regex_trace = regex_result.get(kpi, {})
        
        source = score_data.get("source")
        page_number = regex_trace.get("page")
        line_text = regex_trace.get("line")
        
        # If the metric was ONLY found by Gemini (and completely missed by Regex),
        # we don't have exact line-level traceability.
        if source == "GEMINI" and not page_number:
            page_number = "LLM Source"
            line_text = "No direct regex trace available"
            
        audit_entry = {
            "kpi": kpi.replace('_', ' ').title(),  # Format kpi nicely, e.g. "net_income" -> "Net Income"
            "value": score_data.get("value"),
            "confidence": score_data.get("confidence"),
            "source": source,
            "page_number": page_number,
            "line_text": line_text
        }
        
        audit_trail.append(audit_entry)
        
    return audit_trail
