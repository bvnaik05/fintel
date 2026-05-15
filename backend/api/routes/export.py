from fastapi import APIRouter

router = APIRouter(prefix="/export", tags=["Export"])

# Placeholder endpoints to prevent router errors
@router.get("/status")
def status():
    return {"status": "placeholder"}
