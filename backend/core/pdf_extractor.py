import pdfplumber
import pandas as pd
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def extract_text_by_page(pdf_path: str) -> Dict[int, str]:
    """
    Extracts text from a PDF, returning a dictionary mapping page numbers (1-indexed) to text.
    """
    text_by_page = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    text_by_page[i + 1] = text
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
    return text_by_page

def extract_tables(pdf_path: str) -> List[pd.DataFrame]:
    """
    Extracts tables from a PDF, returning a list of pandas DataFrames.
    """
    tables_list = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_tables = page.extract_tables()
                for table in extracted_tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # Pad rows to have the same length
                    max_cols = max(len(row) for row in table)
                    padded_table = [row + [None] * (max_cols - len(row)) for row in table]
                    
                    # Use the first row as columns. Make sure columns are strings and unique
                    cols = [str(c) if c is not None else f"Unnamed_{i}" for i, c in enumerate(padded_table[0])]
                    
                    df = pd.DataFrame(padded_table[1:], columns=cols)
                    tables_list.append(df)
    except Exception as e:
        logger.error(f"Error extracting tables from {pdf_path}: {e}")
    return tables_list

def find_financial_pages(text_by_page: Dict[int, str]) -> List[int]:
    """
    Uses heuristic keyword matching to identify pages likely containing financial statements
    (e.g., Income Statement, Balance Sheet, Cash Flow).
    """
    financial_keywords = [
        "consolidated statements of income",
        "consolidated statements of operations",
        "consolidated balance sheets",
        "consolidated statements of cash flows",
        "consolidated statement of comprehensive income",
        "statement of financial position"
    ]
    
    financial_pages = []
    for page_num, text in text_by_page.items():
        text_lower = text.lower()
        for keyword in financial_keywords:
            if keyword in text_lower:
                financial_pages.append(page_num)
                break
                
    return financial_pages
