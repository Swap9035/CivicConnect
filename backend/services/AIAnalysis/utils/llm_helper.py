from langchain_mistralai import ChatMistralAI
from services.AIAnalysis.utils.config import settings

def get_mistral_llm(temperature: float = 0.3):
    """Initialize and return Mistral LLM instance"""
    return ChatMistralAI(
        model="mistral-medium-latest",
        mistral_api_key=settings.MISTRAL_API_KEY,
        temperature=temperature
    )
