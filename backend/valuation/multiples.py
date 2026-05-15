import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

def safe_divide(numerator: float, denominator: float) -> float:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return float(numerator) / float(denominator)

def ev_ebitda(ev: float, ebitda: float) -> float:
    return safe_divide(ev, ebitda)

def ev_revenue(ev: float, revenue: float) -> float:
    return safe_divide(ev, revenue)

def pe_ratio(price: float, eps: float) -> float:
    return safe_divide(price, eps)

def p_book(price: float, book_per_share: float) -> float:
    return safe_divide(price, book_per_share)

def compute_peer_multiples(peer_df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies valuation multiple calculations to every row in the peer dataframe.
    """
    df = peer_df.copy()
    
    # Helper to calculate EPS from net income and shares outstanding
    def calc_eps(row):
        return safe_divide(row.get('net_income'), row.get('shares_outstanding'))
        
    df['eps'] = df.apply(calc_eps, axis=1)
    
    # Calculate multiples
    df['ev_ebitda'] = df.apply(lambda row: ev_ebitda(row.get('enterprise_value'), row.get('ebitda')), axis=1)
    df['ev_revenue'] = df.apply(lambda row: ev_revenue(row.get('enterprise_value'), row.get('revenue')), axis=1)
    df['pe_ratio'] = df.apply(lambda row: pe_ratio(row.get('current_price'), row.get('eps')), axis=1)
    df['p_book'] = df.apply(lambda row: p_book(row.get('current_price'), row.get('book_value')), axis=1)
    
    return df

def apply_median_multiple(target_kpi: Dict[str, Any], peer_multiples_df: pd.DataFrame) -> Dict[str, Tuple[float, float]]:
    """
    Uses peer quartile multiples (25th and 75th percentiles) to return implied Equity Value ranges
    for the target company.
    
    Bridges EV to Equity Value using: Equity Value = EV - Total Debt + Cash & Equivalents
    """
    ranges = {}
    
    # Helper to safely extract values from the confidence_scorer output dictionary format
    def get_val(keys: list):
        for key in keys:
            kpi = target_kpi.get(key)
            if isinstance(kpi, dict) and "value" in kpi:
                if kpi["value"] is not None:
                    return float(kpi["value"])
            elif kpi is not None:
                return float(kpi)
        return None
        
    revenue = get_val(["revenue", "Revenue"])
    ebitda = get_val(["ebitda", "Ebitda", "EBITDA"])
    net_income = get_val(["net_income", "Net Income"])
    book_value = get_val(["book_value", "Book Value"]) # Note: usually total equity here
    
    debt = get_val(["total_debt", "Total Debt"]) or 0.0
    cash = get_val(["cash_and_equivalents", "Cash And Equivalents"]) or 0.0
    
    # Bridge EV to Equity Value
    def ev_to_eqv(ev_value):
        return ev_value - debt + cash
        
    def get_percentiles(col):
        # Drop NAs and negative multiples (implausible)
        if col not in peer_multiples_df.columns:
            return None, None
        valid = peer_multiples_df[col].dropna()
        valid = valid[valid > 0]
        if valid.empty:
            return None, None
        return np.percentile(valid, 25), np.percentile(valid, 75)
        
    # 1. EV / EBITDA
    if ebitda:
        p25, p75 = get_percentiles('ev_ebitda')
        if p25 and p75:
            implied_ev_low = p25 * ebitda
            implied_ev_high = p75 * ebitda
            ranges["EV/EBITDA"] = (ev_to_eqv(implied_ev_low), ev_to_eqv(implied_ev_high))
            
    # 2. EV / Revenue
    if revenue:
        p25, p75 = get_percentiles('ev_revenue')
        if p25 and p75:
            implied_ev_low = p25 * revenue
            implied_ev_high = p75 * revenue
            ranges["EV/Revenue"] = (ev_to_eqv(implied_ev_low), ev_to_eqv(implied_ev_high))
            
    # 3. P/E Ratio
    if net_income:
        p25, p75 = get_percentiles('pe_ratio')
        if p25 and p75:
            # P/E * Net Income = Equity Value directly
            ranges["P/E Ratio"] = (p25 * net_income, p75 * net_income)
            
    # 4. P/Book
    if book_value:
        p25, p75 = get_percentiles('p_book')
        if p25 and p75:
            # P/B * Total Book Value = Equity Value directly
            ranges["P/Book"] = (p25 * book_value, p75 * book_value)
            
    return ranges
