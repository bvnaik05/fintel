# FinTel-CCA — Automated Financial Statement Ingestion & Comparable Company Analysis

> Inspired by portfolio valuation workflows in private credit and alternative asset management.

## What This Does
- Ingests SEC 10-K filings (PDF) and extracts 15+ financial KPIs using pdfplumber + Google Gemini Flash
- Source-level auditability: every extracted number is traced to its exact page and line
- Confidence scoring: cross-references regex extraction vs LLM extraction (HIGH / MEDIUM / LOW)
- Comparable company analysis: fetches live peer data via yfinance, computes EV/EBITDA, P/E, P/Book, EV/Revenue
- Football field valuation chart showing implied equity value ranges across methodologies
- Mark deviation alert: flags when implied fair value deviates >15% from reported book value
- Analyst-ready Excel export with 4 sheets: KPIs, Audit Trail, Comps, Valuation

## Tech Stack
Python · FastAPI · Google Gemini Flash · pdfplumber · yfinance · pandas · plotly · openpyxl · React

## Demo
[Add screenshot of football field chart here]
[Add screenshot of Swagger UI here]
[Add screenshot of deviation alert here]

## Run Locally
\```bash
cd backend && uvicorn main:app --reload
cd frontend && npm run dev
\```