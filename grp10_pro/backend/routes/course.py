from fastapi import APIRouter
from backend.tools.course_tool import get_course

router = APIRouter(prefix="/course", tags=["Course"])

@router.get("/")
def course(code: str):
    result = get_course(code)
    return {
        "course_code": code,
        "data": result
    }