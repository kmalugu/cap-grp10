from fastapi import APIRouter
from backend.tools.fees_tool import get_fees

router = APIRouter(prefix="/fees", tags=["Fees"])

@router.get("/")
def fees(program: str, nationality: str = "domestic"):
    result = get_fees(program, nationality)
    return {
        "program": program,
        "nationality": nationality,
        "data": result
    }