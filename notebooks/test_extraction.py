import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from core.pdf_extractor import extract_text_by_page, find_financial_pages
from core.regex_pipeline import extract_kpis_with_regex
from core.gemini_parser import parse_financials

def test_extraction():
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_10k', 'apple_10k_2023.pdf'))
    print(f"Extracting text from {pdf_path}...")
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    text_by_page = extract_text_by_page(pdf_path)
    print(f"Total pages extracted: {len(text_by_page)}")

    fin_pages = find_financial_pages(text_by_page)
    print(f"Financial pages found at: {fin_pages}")

    regex_results = extract_kpis_with_regex(text_by_page)
    print("\n--- Regex Extraction Results ---")
    for kpi, data in regex_results.items():
        print(f"[{kpi.upper()}] {data['value']} (Page {data['page']})")
        print(f"    Line: {data['line']}")
        
    print("\n--- Gemini Extraction Test ---")
    if fin_pages:
        # Test Gemini extraction on the actual income statement page
        page_to_test = 31
        text_chunk = text_by_page[page_to_test]
        print(f"Sending Page {page_to_test} to Gemini...")
        
        gemini_results = parse_financials(text_chunk, "Apple")
        print("Gemini Output:")
        print(gemini_results)
        
        print("\n--- Confidence Scorer & Auditor ---")
        from core.confidence_scorer import score_kpis
        from core.auditor import build_audit_trail
        
        scored_kpis = score_kpis(regex_results, gemini_results)
        audit_trail = build_audit_trail(regex_results, scored_kpis)
        
        import json
        print(json.dumps(audit_trail, indent=2))
        
    else:
        print("No financial pages found to test Gemini.")

if __name__ == "__main__":
    test_extraction()
