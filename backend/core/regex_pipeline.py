import re
from typing import Dict, Any

# Regex patterns updated to optionally capture multiplier words
PATTERNS = {
    "revenue": r"(?i)(?:total\s+)?(?:net\s+)?(?:sales|revenue)[s]?\s+\$?([\d,\.]+)\s*(million|billion|thousand|in\s+thousands)?",
    "net_income": r"(?i)net\s+income\s+\$?([\d,\.]+)\s*(million|billion|thousand|in\s+thousands)?",
    "ebit": r"(?i)operating\s+income\s+\$?([\d,\.]+)\s*(million|billion|thousand|in\s+thousands)?",
    "ebitda": r"(?i)ebitda\s+\$?([\d,\.]+)\s*(million|billion|thousand|in\s+thousands)?",
    "total_debt": r"(?i)(?:total\s+)?(?:term\s+)?debt\s+\$?([\d,\.]+)\s*(million|billion|thousand|in\s+thousands)?",
    "cash_and_equivalents": r"(?i)cash\s+and\s+cash\s+equivalents\s+\$?([\d,\.]+)\s*(million|billion|thousand|in\s+thousands)?",
    "capex": r"(?i)(?:payments\s+for\s+)?(?:acquisition\s+of\s+)?property,\s+plant\s+and\s+equipment\s+\$?([\d,\.]+)\s*(million|billion|thousand|in\s+thousands)?",
    "shares_outstanding": r"(?i)(?:weighted-average\s+)?shares\s+(?:outstanding\s+)?(?:-|–|—)?\s+(?:basic|diluted)\s+([\d,\.]+)\s*(million|billion|thousand|in\s+thousands)?"
}

def clean_value(val_str: str, multiplier: str) -> float:
    try:
        val = float(val_str.replace(',', '').strip())
        if multiplier:
            mult = multiplier.lower()
            if 'billion' in mult:
                val *= 1000 # normalise to millions
            elif 'thousand' in mult:
                val /= 1000 # normalise to millions
        return val
    except ValueError:
        return None

def extract_kpis_with_regex(text_by_page: Dict[int, str]) -> Dict[str, Any]:
    """
    Extracts KPIs from text using regular expressions.
    Returns: dict[kpi_name, {"value": float, "page": int, "line": str, "raw_match": str}]
    """
    results = {}
    
    # Simple heuristic to find a page-level multiplier
    page_multipliers = {}
    for page_num, text in text_by_page.items():
        text_lower = text.lower()
        if "in thousands" in text_lower or "thousands," in text_lower:
            page_multipliers[page_num] = "thousand"
        elif "in millions" in text_lower or "millions," in text_lower:
            page_multipliers[page_num] = "million"
        elif "in billions" in text_lower:
            page_multipliers[page_num] = "billion"
            
    for kpi, pattern in PATTERNS.items():
        found = False
        # Search through pages
        for page_num, text in text_by_page.items():
            if found:
                break
                
            page_mult = page_multipliers.get(page_num, None)
            lines = text.split('\n')
            for line in lines:
                match = re.search(pattern, line)
                if match:
                    val_str = match.group(1)
                    inline_mult = match.group(2) if len(match.groups()) > 1 else None
                    
                    # Prefer inline multiplier over page multiplier
                    active_mult = inline_mult if inline_mult else page_mult
                    
                    val = clean_value(val_str, active_mult)
                    if val is not None:
                        results[kpi] = {
                            "value": val,
                            "page": page_num,
                            "line": line.strip(),
                            "raw_match": match.group(0)
                        }
                        found = True
                        break
                        
    return results
