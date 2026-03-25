from fastapi import APIRouter
from backend.tools.calendar_tool import get_calendar

router = APIRouter(prefix="/calendar", tags=["Calendar"])

@router.get("/")
def calendar(program: str):
    result = get_calendar(program)
    return {
        "program": program,
        "events": result
    }