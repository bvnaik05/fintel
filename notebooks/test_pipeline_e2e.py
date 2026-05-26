"""
End-to-end pipeline test: Upload Apple 10-K → Poll Status → Fetch Results
"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000"
PDF_PATH = r"C:\Users\naikb\OneDrive\Desktop\Projects\Fintel\fintel\data\sample_10k\apple_10k_2023.pdf"

def main():
    # ── Step 1: Upload the PDF ──
    print("=" * 60)
    print("STEP 1: Uploading Apple 10-K PDF...")
    print("=" * 60)
    
    with open(PDF_PATH, "rb") as f:
        files = {"file": ("apple_10k_2023.pdf", f, "application/pdf")}
        data = {"company_name": "Apple Inc."}
        resp = requests.post(f"{BASE_URL}/ingest/upload", files=files, data=data)
    
    if resp.status_code != 200:
        print(f"Upload FAILED: {resp.status_code} — {resp.text}")
        return
    
    job_id = resp.json()["job_id"]
    print(f"Upload OK. Job ID: {job_id}")
    
    # ── Step 2: Poll status until DONE ──
    print("\n" + "=" * 60)
    print("STEP 2: Polling job status...")
    print("=" * 60)
    
    for attempt in range(1, 31):  # Max 30 attempts = 60 seconds
        time.sleep(2)
        status_resp = requests.get(f"{BASE_URL}/ingest/{job_id}/status")
        status_data = status_resp.json()
        status = status_data["status"]
        print(f"  Attempt {attempt}: {status}")
        
        if status == "DONE":
            break
        elif status == "FAILED":
            print(f"  ERROR: {status_data.get('error', 'Unknown error')}")
            return
    else:
        print("  TIMEOUT: Job did not complete within 60 seconds.")
        return
    
    # ── Step 3: Fetch results ──
    print("\n" + "=" * 60)
    print("STEP 3: Fetching extracted KPIs + Audit Trail...")
    print("=" * 60)
    
    results_resp = requests.get(f"{BASE_URL}/ingest/{job_id}/results")
    
    if results_resp.status_code != 200:
        print(f"Results FAILED: {results_resp.status_code} — {results_resp.text}")
        return
    
    results = results_resp.json()
    
    # Print KPIs
    print("\n-- Extracted KPIs --")
    for kpi, data in results["extracted_kpis"].items():
        val = data.get("value")
        conf = data.get("confidence")
        src = data.get("source")
        delta = data.get("delta_pct")
        print(f"  {kpi:30s} | Value: {str(val):>15s} | Confidence: {conf:6s} | Source: {src:6s} | Delta: {delta}")
    
    # Print Audit Trail
    print("\n-- Audit Trail --")
    for entry in results["audit_trail"]:
        kpi = entry.get("kpi", "")
        page = entry.get("page_number", "?")
        conf = entry.get("confidence", "?")
        line = entry.get("line_text", "")[:80]
        print(f"  {kpi:30s} | Page: {str(page):>4s} | Confidence: {conf:6s} | Line: {line}")
    
    print("\n" + "=" * 60)
    print("PIPELINE TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
