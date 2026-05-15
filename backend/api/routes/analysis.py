from fastapi import APIRouter

router = APIRouter(prefix="/analyze", tags=["Analysis"])

# Placeholder endpoints to prevent router errors
@router.get("/status")
def status():
    return {"status": "placeholder"}
