import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from valuation.data_fetcher import fetch_peer_set
from valuation.multiples import compute_peer_multiples

def run_test():
    tickers = ["AAPL", "MSFT", "GOOGL", "META", "NVDA"]
    print(f"Fetching data for peers: {tickers}...")
    df = fetch_peer_set(tickers)
    
    print("\nComputing multiples...")
    df = compute_peer_multiples(df)
    
    print("\nFinal Multiples Table:")
    print(df[["ticker", "ev_ebitda", "ev_revenue", "pe_ratio", "p_book"]])

if __name__ == "__main__":
    run_test()
