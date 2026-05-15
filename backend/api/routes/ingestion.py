import os
import uuid
import shutil
import logging
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException

from core.pdf_extractor import extract_text_by_page, find_financial_pages
from core.regex_pipeline import extract_kpis_with_regex
from core.gemini_parser import parse_financials
from core.confidence_scorer import score_kpis
from core.auditor import build_audit_trail

router = APIRouter(prefix="/ingest", tags=["Ingestion"])
logger = logging.getLogger(__name__)

# In-memory storage for jobs
# Format: { "job_id": {"status": "PENDING", "results": None, "error": None} }
JOB_STORE = {}

# Temp directory for processing PDFs
TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

def process_pdf_pipeline(job_id: str, file_path: str, company_name: str):
    """Background task to execute the end-to-end Part A Document Intelligence pipeline."""
    try:
        JOB_STORE[job_id]["status"] = "RUNNING"
        
        # 1. PDF Extraction
        pages = extract_text_by_page(file_path)
        financial_pages = find_financial_pages(pages)
        
        if not financial_pages:
            raise ValueError("Could not locate any financial statement pages in the PDF.")
            
        # 2. Regex Extraction (runs on all identified financial pages)
        regex_result = extract_kpis_with_regex(pages, financial_pages)
        
        # 3. Gemini LLM Extraction (target the core income statement page)
        # Note: In a 10-K, the Income Statement is often the 2nd financial page identified
        page_to_send = financial_pages[1] if len(financial_pages) > 1 else financial_pages[0]
        text_chunk = pages[page_to_send]
        
        gemini_result = parse_financials(text_chunk, company_name)
        
        # 4. Cross-Reference Confidence Scorer
        scored_kpis = score_kpis(regex_result, gemini_result)
        
        # 5. Audit Trail Builder
        audit_trail = build_audit_trail(regex_result, scored_kpis)
        
        # Save exact JSON payload
        JOB_STORE[job_id]["results"] = {
            "extracted_kpis": scored_kpis,
            "audit_trail": audit_trail
        }
        JOB_STORE[job_id]["status"] = "DONE"
        
    except Exception as e:
        logger.error(f"Pipeline failed for job {job_id}: {str(e)}")
        JOB_STORE[job_id]["status"] = "FAILED"
        JOB_STORE[job_id]["error"] = str(e)
    finally:
        # Cleanup temp PDF file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    company_name: str = Form("Target Company")
):
    """Uploads a 10-K PDF and kicks off the background extraction pipeline."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    job_id = str(uuid.uuid4())
    
    # Initialize job in store
    JOB_STORE[job_id] = {"status": "PENDING", "results": None, "error": None}
    
    # Save file safely to temp dir
    file_path = os.path.join(TEMP_DIR, f"{job_id}.pdf")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Kick off asynchronous background task so the route returns instantly
    background_tasks.add_task(process_pdf_pipeline, job_id, file_path, company_name)
    
    return {"job_id": job_id}


@router.get("/{job_id}/status")
def get_status(job_id: str):
    """Polls the status of an ongoing extraction job."""
    job = JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    response = {"status": job["status"]}
    if job["status"] == "FAILED":
        response["error"] = job.get("error")
        
    return response


@router.get("/{job_id}/results")
def get_results(job_id: str):
    """Retrieves the final structured extraction payload."""
    job = JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job["status"] != "DONE":
        raise HTTPException(status_code=400, detail=f"Job is not finished. Current status: {job['status']}")
        
    return job["results"]
