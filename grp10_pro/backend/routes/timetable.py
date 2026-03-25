from fastapi import APIRouter
from backend.tools.timetable_tool import get_timetable

router = APIRouter(prefix="/timetable", tags=["Timetable"])

@router.get("/")
def timetable(year: int, department: str):
    result = get_timetable(year, department)
    return {
        "year": year,
        "department": department,
        "data": result
    }