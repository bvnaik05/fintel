from typing import Dict, Any, Optional, Tuple

def check_deviation(valuation_ranges: Dict[str, Tuple[float, float]], book_value: float) -> Optional[Dict[str, Any]]:
    """
    Computes the midpoint across all valuation methodology ranges and checks for 
    significant deviations against the company's current reported book value.
    
    Args:
        valuation_ranges: Dict mapping methodologies to (low, high) tuples.
        book_value: Current reported book value.
        
    Returns:
        Dict containing severity, deviation_pct, implied_mid, book_value, and message.
        Returns None if the deviation is within normal parameters (< 15%).
    """
    if not valuation_ranges or not book_value or book_value == 0:
        return None
        
    # Calculate the overall midpoint across all available methodologies
    mids = []
    for low, high in valuation_ranges.values():
        mids.append((low + high) / 2.0)
        
    if not mids:
        return None
        
    overall_mid = sum(mids) / len(mids)
    
    # Calculate absolute deviation percentage
    deviation = abs((overall_mid - book_value) / book_value)
    
    # Determine severity
    if deviation > 0.30:
        severity = "HIGH"
    elif deviation >= 0.15:
        severity = "MEDIUM"
    else:
        return None  # Deviation is under 15%, no alert needed
        
    deviation_pct = round(deviation * 100, 1)
    
    # Format a clean, analyst-friendly alert message
    message = f"Implied fair value (${overall_mid:,.0f}M) deviates {deviation_pct}% from reported book value (${book_value:,.0f}M)."
    
    return {
        "severity": severity,
        "deviation_pct": deviation_pct,
        "implied_mid": round(overall_mid, 2),
        "book_value": round(book_value, 2),
        "message": message
    }
