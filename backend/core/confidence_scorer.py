from typing import Dict, Any

def score_kpis(regex_result: Dict[str, Any], gemini_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scores the confidence of extracted KPIs by comparing regex results against Gemini results.
    
    Inputs:
    - regex_result: Dict from regex_pipeline.py (format: {kpi: {"value": float, ...}})
    - gemini_result: Dict from gemini_parser.py (format: {kpi: float})
    
    Returns:
    - Dict[str, dict]: {kpi: {"value": float, "confidence": str, "source": str, "delta_pct": float}}
    """
    # KPIs that should logically never be negative
    non_negative_kpis = {"revenue", "total_debt", "cash_and_equivalents", "shares_outstanding", "capex"}
    
    all_kpis = set(regex_result.keys()).union(set(gemini_result.keys()))
    # Remove metadata keys from Gemini result
    all_kpis.discard("fiscal_year")
    all_kpis.discard("currency")
    
    scored_results = {}
    
    for kpi in all_kpis:
        # Extract values
        reg_data = regex_result.get(kpi)
        reg_val = reg_data.get("value") if isinstance(reg_data, dict) else None
        
        gem_val = gemini_result.get(kpi)
        
        confidence = "LOW"
        final_value = None
        source = "NONE"
        delta_pct = None
        
        # Helper to flag mathematically impossible KPIs
        def is_implausible(val):
            return val is not None and kpi in non_negative_kpis and val < 0

        # Skip if neither pipeline found the KPI
        if reg_val is None and gem_val is None:
            continue
            
        # Both pipelines found a value
        if reg_val is not None and gem_val is not None:
            source = "BOTH"
            final_value = gem_val  # Default to Gemini as source of truth
            
            if gem_val == 0 and reg_val == 0:
                delta = 0.0
            elif gem_val == 0:
                delta = float('inf')  # Prevent division by zero
            else:
                delta = abs(reg_val - gem_val) / abs(gem_val)
                
            delta_pct = round(delta * 100, 2)
            
            if is_implausible(gem_val) or is_implausible(reg_val):
                confidence = "LOW"
            elif delta <= 0.02:   # Within 2%
                confidence = "HIGH"
            elif delta <= 0.20:   # Within 20%
                confidence = "MEDIUM"
            else:                 # >20% deviation
                confidence = "LOW"
                
        # Only Gemini found a value
        elif gem_val is not None:
            source = "GEMINI"
            final_value = gem_val
            delta_pct = None
            
            if is_implausible(gem_val):
                confidence = "LOW"
            else:
                confidence = "MEDIUM"
                
        # Only Regex found a value
        elif reg_val is not None:
            source = "REGEX"
            final_value = reg_val
            delta_pct = None
            
            if is_implausible(reg_val):
                confidence = "LOW"
            else:
                confidence = "MEDIUM"
                
        scored_results[kpi] = {
            "value": final_value,
            "confidence": confidence,
            "source": source,
            "delta_pct": delta_pct
        }
        
    return scored_results
