from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import chat, course, timetable, fees, calendar, rag, faculty

app = FastAPI(title="University AI Assistant")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(chat.router)
app.include_router(course.router)
app.include_router(timetable.router)
app.include_router(fees.router)
app.include_router(calendar.router)
app.include_router(rag.router)
app.include_router(faculty.router)

@app.get("/")
def home():
    return {"message": "University AI Assistant API is running"}