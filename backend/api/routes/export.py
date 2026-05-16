import os
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.routes.ingestion import JOB_STORE
from api.routes.analysis import ANALYSIS_STORE
from utils.excel_exporter import export_to_excel

router = APIRouter(prefix="/export", tags=["Export"])

# Directory to save exports temporarily
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

@router.get("/{job_id}/excel")
def export_excel(job_id: str):
    """Generates the formatted 4-sheet Excel deliverable and returns it as a file download."""
    job = JOB_STORE.get(job_id)
    analysis = ANALYSIS_STORE.get(job_id)
    
    if not job or job.get("status") != "DONE":
        raise HTTPException(status_code=400, detail="Ingestion job not finished or not found.")
        
    if not analysis or analysis.get("status") != "DONE":
        raise HTTPException(status_code=400, detail="Analysis job not finished or not found.")
        
    # Extract data from state
    extracted_kpis = job["results"]["extracted_kpis"]
    audit_trail = job["results"]["audit_trail"]
    
    comps_dict = analysis["comps"]
    # Reconstruct pandas DataFrame from the JSON dictionaries
    peer_multiples_df = pd.DataFrame(comps_dict)
    
    valuation_ranges = analysis["valuation_ranges"]
    
    # Helper to pull the book value safely for the final row
    def get_book_value():
        for key in ["book_value", "Book Value", "total_equity", "Total Equity"]:
            kpi = extracted_kpis.get(key)
            if isinstance(kpi, dict) and "value" in kpi and kpi["value"] is not None:
                return float(kpi["value"])
        return None
        
    # Generate unique output path
    output_path = os.path.join(EXPORT_DIR, f"valuation_model_{job_id}.xlsx")
    
    # Run the exporter script
    export_to_excel(
        extracted_kpis=extracted_kpis,
        audit_trail=audit_trail,
        peer_multiples_df=peer_multiples_df,
        valuation_ranges=valuation_ranges,
        output_path=output_path,
        book_value=get_book_value()
    )
    
    # Return as direct file download
    return FileResponse(
        path=output_path,
        filename=f"FinTel_Valuation_Model_{job_id[:8]}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
