from langchain_openai import ChatOpenAI
from services.AIAnalysis.utils.config import settings

def get_mistral_llm(temperature: float = 0.3):
    """Initialize and return Mistral LLM instance via OpenRouter"""
    return ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base=settings.OPENROUTER_BASE_URL,
        temperature=temperature,
        default_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "CivicConnect AI",
        },
    )

