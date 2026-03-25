# LLM Setup (Gemini 2.5 Flash)
from langchain_google_genai import ChatGoogleGenerativeAI

from utils.config import GEMINI_MODEL, GOOGLE_API_KEY, LLM_TEMPERATURE

_llm_cache = None


def _extract_text(response) -> str:
    """Normalize LangChain chat responses into plain text for existing callers."""
    if isinstance(response, str):
        return response.strip()

    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
            else:
                text = getattr(item, "text", None)
                if text:
                    parts.append(text)

        combined = "".join(parts).strip()
        if combined:
            return combined

    return str(content).strip()


class GeminiChatService:
    """Small wrapper to preserve the project's existing `invoke(prompt) -> str` API."""

    def __init__(self):
        if not GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is not set. Add it to your .env file before starting the app."
            )

        self.client = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=LLM_TEMPERATURE,
        )

    def invoke(self, prompt: str) -> str:
        response = self.client.invoke(prompt)
        return _extract_text(response)


def get_llm():
    """Return a cached Gemini 2.5 Flash client wrapper."""
    global _llm_cache

    if _llm_cache is None:
        _llm_cache = GeminiChatService()

    return _llm_cache
