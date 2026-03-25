from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.rag_pipeline import rag_answer

router = APIRouter(prefix="/rag", tags=["RAG"])

class RagRequest(BaseModel):
    query: str

@router.post("/")
def rag(req: RagRequest):
    try:
        answer = rag_answer(req.query)
        return {
            "query": req.query,
            "response": answer
        }
    except Exception as e:
        print(f"RAG Error: {str(e)}")
        return {
            "query": req.query,
            "response": f"Error processing query: {str(e)}",
            "error": True
        }