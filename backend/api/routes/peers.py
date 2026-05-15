from fastapi import APIRouter

router = APIRouter(prefix="/peers", tags=["Peers"])

# Placeholder endpoints to prevent router errors
@router.get("/status")
def status():
    return {"status": "placeholder"}
