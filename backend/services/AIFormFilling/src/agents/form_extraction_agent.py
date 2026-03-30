import os
import json
import re
from typing import Optional
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from ..utils.prompts import EXTRACTION_PROMPT, CLARIFICATION_PROMPT, FORM_COMPLETION_CHECK_PROMPT
from ..db.models import AgentResponse

load_dotenv()

class FormExtractionAgent:
    def __init__(self):
        self.llm = ChatMistralAI(
            model="mistral-large-latest",
            mistral_api_key=os.getenv("MISTRAL_API_KEY"),
            temperature=0.1
        )
    
    async def extract_from_text(self, input_text: str, additional_context: str = "") -> dict:
        """Extract structured data from unstructured grievance text."""
        prompt = EXTRACTION_PROMPT.format(
            input_text=input_text,
            additional_context=additional_context
        )
        
        messages = [
            SystemMessage(content="You are a helpful assistant that extracts structured data from grievance complaints. Always respond with valid JSON only."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            # Parse the JSON response
            result = self._parse_json_response(response.content)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "error": "Failed to parse response",
                "raw_response": response.content,
                "missing_info": ["all fields"],
                "clarification_questions": ["Could you please describe your grievance in more detail?"]
            }
    
    async def process_clarification(self, current_data: dict, missing_info: list, user_response: str) -> dict:
        """Process user's clarification response and update form data."""
        prompt = CLARIFICATION_PROMPT.format(
            current_data=json.dumps(current_data, indent=2),
            missing_info=json.dumps(missing_info),
            user_response=user_response
        )
        
        messages = [
            SystemMessage(content="You are a helpful assistant updating grievance form data based on user clarifications. Always respond with valid JSON only."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result = self._parse_json_response(response.content)
            return result
        except json.JSONDecodeError:
            return {
                "updated_fields": {},
                "still_missing": missing_info,
                "new_questions": ["I couldn't understand your response. Could you please clarify?"],
                "is_complete": False
            }
    
    async def check_form_completion(self, form_data: dict) -> dict:
        """Check if the form has all required information."""
        prompt = FORM_COMPLETION_CHECK_PROMPT.format(
            form_data=json.dumps(form_data, indent=2)
        )
        
        messages = [
            SystemMessage(content="You are a form validation assistant. Always respond with valid JSON only."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            return self._parse_json_response(response.content)
        except json.JSONDecodeError:
            # Manual check as fallback
            required_fields = ['title', 'category', 'full_description']
            location_fields = ['landmark', 'location_hint', 'area_ward_name']
            
            missing = [f for f in required_fields if not form_data.get(f)]
            has_location = any(form_data.get(f) for f in location_fields)
            
            if not has_location:
                missing.append("location (landmark, area, or location hint)")
            
            return {
                "is_complete": len(missing) == 0,
                "missing_critical_fields": missing,
                "suggested_questions": [f"Please provide: {field}" for field in missing]
            }
    
    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks and cleaning invalid syntax."""
        content = content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        # Remove JavaScript-style comments (// ...)
        content = re.sub(r'//.*', '', content)
        
        # Remove trailing commas before closing braces/brackets
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        
        # Attempt to parse JSON
        return json.loads(content)
