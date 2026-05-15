import os
import json
import logging
import google.generativeai as genai
from typing import Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

EXTRACTION_PROMPT = """
You are a financial data extraction specialist. From the 10-K text below,
extract ONLY these fields for the most recent fiscal year.

Return ONLY valid JSON — no preamble, no markdown, no explanation:
{{
  "revenue": <number in millions USD or null>,
  "ebitda": <number in millions USD or null>,
  "ebit": <number in millions USD or null>,
  "net_income": <number in millions USD or null>,
  "total_debt": <number in millions USD or null>,
  "cash_and_equivalents": <number in millions USD or null>,
  "capex": <number in millions USD or null>,
  "fiscal_year": <YYYY integer>,
  "currency": <"USD" or ISO code>
}}

Text:
{text_chunk}
"""

def parse_financials(text_chunk: str, company_name: str = "Target Company") -> Dict[str, Any]:
    """
    Sends the financial page text to Gemini Flash and asks it to return structured JSON.
    """
    if not api_key:
        logger.error("GEMINI_API_KEY is not set.")
        return {}

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = EXTRACTION_PROMPT.format(text_chunk=text_chunk)
        
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Clean up markdown if Gemini returned it despite instructions
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        return json.loads(content)
        
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return {}
