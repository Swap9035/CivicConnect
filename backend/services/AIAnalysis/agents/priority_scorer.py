from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Literal
from services.AIAnalysis.shared.schemas import GrievanceData, PriorityScore
from services.AIAnalysis.utils.llm_helper import get_mistral_llm
import json

class PriorityScoreOutput(BaseModel):
    score: int = Field(description="Numerical severity score from 0-100")
    reasoning: str = Field(description="Explanation for the score")
    urgency_level: Literal["low", "medium", "high", "critical"] = Field(
        description="Urgency classification"
    )

class PriorityScorerAgent:
    def __init__(self):
        self.llm = get_mistral_llm(temperature=0.2)
        self.parser = PydanticOutputParser(pydantic_object=PriorityScoreOutput)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert grievance priority analyzer for a municipal corporation.
Your task is to assign a numerical severity score (0-100) based on:
1. Impacted Population (higher impact = higher score)
2. Category (safety issues like live wires = highest priority)
3. Is Recurring (recurring issues get +20 bonus points)

Scoring Guidelines:
- 90-100: Critical (Life-threatening, entire colony affected)
- 70-89: High (Safety risk, large area affected)
- 40-69: Medium (Quality of life, moderate area)
- 0-39: Low (Minor issues, single household)

{format_instructions}"""),
            ("human", """Analyze this grievance and provide a priority score:

Title: {title}
Description: {description}
Category: {category}
Impacted Population: {impacted_population}
Is Recurring: {is_recurring}

Provide your analysis in JSON format.""")
        ])
    
    async def score_priority(self, grievance: GrievanceData) -> PriorityScore:
        """
        Analyze grievance and assign priority score using LLM
        """
        try:
            formatted_prompt = self.prompt.format_messages(
                format_instructions=self.parser.get_format_instructions(),
                title=grievance.title,
                description=grievance.full_description,
                category=grievance.category,
                impacted_population=grievance.impacted_population,
                is_recurring=grievance.is_recurring
            )
            
            response = self.llm.invoke(formatted_prompt)
            parsed = self.parser.parse(response.content)
            
            return PriorityScore(
                score=parsed.score,
                reasoning=parsed.reasoning,
                urgency_level=parsed.urgency_level
            )
            
        except Exception as e:
            # Fallback scoring logic
            score = self._fallback_score(grievance)
            return PriorityScore(
                score=score,
                reasoning=f"Fallback scoring applied due to parsing error: {str(e)}",
                urgency_level=self._get_urgency_level(score)
            )
    
    def _fallback_score(self, grievance: GrievanceData) -> int:
        """Simple rule-based fallback scoring"""
        score = 50  # Base score
        
        # Category-based adjustment
        high_priority_categories = ["Electricity", "Water Supply", "Public Safety"]
        if grievance.category in high_priority_categories:
            score += 20
        
        # Population impact
        if "colony" in grievance.impacted_population.lower():
            score += 20
        elif "street" in grievance.impacted_population.lower():
            score += 10
        
        # Recurring bonus
        if grievance.is_recurring:
            score += 15
        
        return min(score, 100)
    
    def _get_urgency_level(self, score: int) -> str:
        if score >= 90:
            return "critical"
        elif score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"
