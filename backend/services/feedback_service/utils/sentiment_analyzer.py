import os
import re
import json
import logging
from typing import Dict
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# New imports for latest LangChain MistralAI
try:
    from langchain_mistralai import ChatMistralAI
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_core.output_parsers import PydanticOutputParser
    _HAS_MISTRAL = True
except ImportError:
    _HAS_MISTRAL = False

class SentimentOutput(BaseModel):
    label: str
    score: float
    explanation: str

def analyze_sentiment(text: str) -> Dict:
    """
    Return a dict: {"label": "positive"|"neutral"|"negative", "score": float (0..1, higher = more negative), "explanation": str}
    Uses LangChain MistralAI if available, otherwise a simple heuristic fallback.
    """
    if not text:
        return {"label": "neutral", "score": 0.5, "explanation": "no text"}

    try:
        if not _HAS_MISTRAL:
            # simple fallback heuristic: count negative words relative to text length
            negative_words = ["bad", "poor", "terrible", "worst", "not", "never", "angry", "disappointed", "unhappy"]
            lowered = text.lower()
            hits = sum(lowered.count(w) for w in negative_words)
            score = min(1.0, hits / max(1, len(lowered.split())))
            label = "negative" if score > 0.25 else ("positive" if "good" in lowered or "great" in lowered else "neutral")
            return {"label": label, "score": float(score), "explanation": "heuristic fallback (langchain not available)"}

        api_key = os.getenv("MISTRAL_API_KEY")
        # Instantiate ChatMistralAI
        llm = ChatMistralAI(api_key=api_key, temperature=0.0)

        # Define output parser
        parser = PydanticOutputParser(pydantic_object=SentimentOutput)

        # Create messages
        system_message = SystemMessage(content="You are a sentiment analysis expert. Classify the sentiment of user feedback and return a JSON object with keys: label (positive|neutral|negative), score (number 0-1 where higher means more negative), and explanation.")
        human_message = HumanMessage(content=f"Feedback:\n\"\"\"\n{text}\n\"\"\"")

        # Invoke and parse
        response = llm.invoke([system_message, human_message])
        parsed = parser.parse(response.content)

        return parsed.dict()

    except Exception as e:
        logger.exception("Sentiment analysis failed")
        return {"label": "neutral", "score": 0.5, "explanation": f"error: {str(e)}"}
