from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
from typing import List, Optional

# Import the in-memory JOB_STORE from ingestion to access the extracted KPIs
from api.routes.ingestion import JOB_STORE

from valuation.data_fetcher import fetch_peer_set
from valuation.multiples import compute_peer_multiples, apply_median_multiple
from valuation.football_field import build_football_field
from valuation.deviation_alert import check_deviation

router = APIRouter(prefix="/analyze", tags=["Analysis"])
logger = logging.getLogger(__name__)

# In-memory storage for analysis results
# Format: { "job_id": {"status": "DONE", "comps": [...], ...} }
ANALYSIS_STORE = {}

class AnalyzeRequest(BaseModel):
    job_id: str
    sector: str
    peer_tickers: List[str]

def process_analysis_pipeline(job_id: str, peer_tickers: List[str]):
    """Background task to run the Part B Comparable Company Analysis engine."""
    try:
        ANALYSIS_STORE[job_id]["status"] = "RUNNING"
        
        # Ensure ingestion is complete and data exists
        job = JOB_STORE.get(job_id)
        if not job or job.get("status") != "DONE":
            raise ValueError(f"Ingestion job {job_id} not found or not finished.")
            
        target_kpis = job["results"]["extracted_kpis"]
        
        # 1. Fetch live peer data via yfinance
        raw_peers_df = fetch_peer_set(peer_tickers)
        
        # 2. Compute valuation multiples for peers
        multiples_df = compute_peer_multiples(raw_peers_df)
        
        # 3. Apply median multiples to target KPIs to get valuation ranges
        valuation_ranges = apply_median_multiple(target_kpis, multiples_df)
        
        # Helper to extract book value for charts/alerts
        def get_book_value():
            for key in ["book_value", "Book Value", "total_equity", "Total Equity"]:
                kpi = target_kpis.get(key)
                if isinstance(kpi, dict) and "value" in kpi and kpi["value"] is not None:
                    return float(kpi["value"])
            return 0.0 # Default fallback if missing
            
        book_value = get_book_value()
        
        # 4. Generate the Plotly Football Field Chart JSON
        chart_dict = build_football_field(valuation_ranges, book_value, "Target Company")
        
        # 5. Check for market deviations
        alert = check_deviation(valuation_ranges, book_value)
        
        # Store all results back into the session
        ANALYSIS_STORE[job_id] = {
            "status": "DONE",
            # Convert DataFrame to list of dicts for JSON serialization
            "comps": multiples_df.replace({float('nan'): None}).to_dict(orient="records"),
            "football_field": chart_dict,
            "deviation_alert": alert,
            "valuation_ranges": valuation_ranges
        }
    except Exception as e:
        logger.error(f"Analysis failed for job {job_id}: {str(e)}")
        ANALYSIS_STORE[job_id] = {
            "status": "FAILED",
            "error": str(e)
        }

@router.post("/run")
async def run_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Triggers the CCA pipeline for a given job and peer set."""
    job_id = request.job_id
    
    # Initialize the store
    ANALYSIS_STORE[job_id] = {"status": "PENDING"}
    
    # Run the heavy yfinance and valuation logic in the background
    background_tasks.add_task(process_analysis_pipeline, job_id, request.peer_tickers)
    
    return {"job_id": job_id}

@router.get("/{job_id}/comps")
def get_comps(job_id: str):
    """Returns the computed peer multiples table."""
    res = ANALYSIS_STORE.get(job_id)
    if not res:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    if res.get("status") != "DONE":
        raise HTTPException(status_code=400, detail="Analysis is still processing or failed")
    return res["comps"]

@router.get("/{job_id}/football-field")
def get_football_field(job_id: str):
    """Returns the JSON required to render the Plotly football field chart."""
    res = ANALYSIS_STORE.get(job_id)
    if not res:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    if res.get("status") != "DONE":
        raise HTTPException(status_code=400, detail="Analysis is still processing or failed")
    return res["football_field"]

@router.get("/{job_id}/deviation-alerts")
def get_deviation_alerts(job_id: str):
    """Returns the deviation alert payload if triggered, otherwise null."""
    res = ANALYSIS_STORE.get(job_id)
    if not res:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    if res.get("status") != "DONE":
        raise HTTPException(status_code=400, detail="Analysis is still processing or failed")
    return res["deviation_alert"]
