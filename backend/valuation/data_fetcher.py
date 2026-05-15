import yfinance as yf
import pandas as pd
import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def fetch_peer_data(ticker: str) -> Dict[str, Any]:
    """
    Fetches financial data for a given ticker using yfinance.
    Gracefully handles missing fields by returning None.
    
    Returns:
        Dict containing ticker, company_name, market_cap, enterprise_value,
        current_price, revenue, ebitda, net_income, book_value, shares_outstanding.
    """
    result = {
        "ticker": ticker.upper(),
        "company_name": None,
        "market_cap": None,
        "enterprise_value": None,
        "current_price": None,
        "revenue": None,
        "ebitda": None,
        "net_income": None,
        "book_value": None,
        "shares_outstanding": None
    }
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info:
            logger.warning(f"No info found for {ticker}")
            return result
            
        # Safely extract data from yfinance info dict
        result["company_name"] = info.get("shortName") or info.get("longName")
        result["market_cap"] = info.get("marketCap")
        result["enterprise_value"] = info.get("enterpriseValue")
        
        # Price can sometimes be under different keys depending on market state
        result["current_price"] = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        
        result["revenue"] = info.get("totalRevenue")
        result["ebitda"] = info.get("ebitda")
        result["net_income"] = info.get("netIncomeToCommon")
        
        # Note: bookValue in yfinance is Book Value Per Share, which is used for P/Book multiple
        result["book_value"] = info.get("bookValue")
        result["shares_outstanding"] = info.get("sharesOutstanding")
        
    except Exception as e:
        logger.error(f"Error fetching data for ticker {ticker}: {e}")
        
    return result

def fetch_peer_set(tickers: List[str]) -> pd.DataFrame:
    """
    Fetches financial data for a list of tickers, adhering to rate limits.
    
    Returns:
        Pandas DataFrame containing the aggregated data for all peers.
    """
    all_data = []
    
    for i, ticker in enumerate(tickers):
        logger.info(f"Fetching data for {ticker} ({i+1}/{len(tickers)})...")
        data = fetch_peer_data(ticker)
        all_data.append(data)
        
        # 1-second sleep to avoid yfinance rate limiting
        if i < len(tickers) - 1:
            time.sleep(1.0)
            
    return pd.DataFrame(all_data)
