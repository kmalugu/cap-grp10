from fastapi import APIRouter
from backend.tools.faculty_tool import get_faculty

router = APIRouter(prefix="/faculty", tags=["Faculty"])

@router.get("/")
def faculty(department: str):
    result = get_faculty(department)
    return {
        "department": department,
        "faculty": result
    }
