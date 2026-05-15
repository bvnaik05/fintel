import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from valuation.football_field import build_football_field
from valuation.deviation_alert import check_deviation

def run_visual_tests():
    # Use Apple's real numbers roughly
    ranges = {
        "EV/EBITDA":  (2800000, 3400000),
        "EV/Revenue": (2600000, 3200000),
        "P/E Ratio":  (2700000, 3500000),
        "P/Book":     (2900000, 3600000),
    }
    book_value = 62_146  # Apple book value in millions

    print("Building Football Field JSON...")
    fig = build_football_field(ranges, book_value, "Apple Inc.")
    print("Chart keys:", list(fig.keys()))  # should print data, layout etc.

    print("\nChecking Deviation...")
    alert = check_deviation(ranges, book_value)
    
    import json
    print("Alert Output:")
    print(json.dumps(alert, indent=2))

if __name__ == "__main__":
    run_visual_tests()
