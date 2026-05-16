import os
import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/peers", tags=["Peers"])

PEERS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "peer_sets")

@router.get("/sectors")
def list_sectors():
    """Returns the predefined list of 5 supported sectors."""
    return ["Tech", "Healthcare", "Consumer", "Energy", "Financials"]

@router.get("/{sector}")
def get_peers_by_sector(sector: str):
    """Reads the pre-seeded CSV file for the requested sector and returns the peer companies."""
    file_name = f"{sector.lower()}_peers.csv"
    file_path = os.path.join(PEERS_DIR, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Peer set for sector '{sector}' not found in data/peer_sets.")
        
    try:
        # Load CSV and convert to JSON dictionary payload
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading peer set: {str(e)}")
