EXTRACTION_PROMPT = """You are an AI assistant that extracts structured grievance information from unstructured citizen complaints.

Your task is to analyze the input text and extract the following fields:

CATEGORY 1 - Core Identification:
- title: A 5-10 word summary of the issue
- category: One of [Sanitation, Water Supply, Electricity, Roads, Public Safety, Other]
- priority: One of [Low, Medium, High] based on urgency
- urgency_reason: Brief explanation for the priority level

CATEGORY 2 - Spatial Data:
- landmark: Nearby landmark mentioned
- location_hint: Any location-related information
- area_ward_name: Area, sector, or ward name if mentioned

CATEGORY 3 - Evidence & Description:
- full_description: Clean, summarized version of the complaint
- incident_datetime: When the issue occurred (if mentioned)

CATEGORY 4 - Actionable Metadata:
- is_recurring: Boolean if this seems like a recurring issue
- impacted_population: One of [Single Household, Street, Entire Colony]

Also identify:
- missing_info: List of critical missing information fields
- clarification_questions: Natural language questions to ask the user for missing info

INPUT TEXT:
{input_text}

ADDITIONAL CONTEXT (if any):
{additional_context}

IMPORTANT: Respond ONLY with a valid JSON object. Do not include any markdown, comments, or explanations. The JSON must be parseable without any extra text.
Example format:
{{
  "title": "...",
  "category": "...",
  "priority": "...",
  "urgency_reason": "...",
  "landmark": "...",
  "location_hint": "...",
  "area_ward_name": "...",
  "full_description": "...",
  "incident_datetime": null,
  "is_recurring": false,
  "impacted_population": "...",
  "missing_info": ["field1", "field2"],
  "clarification_questions": ["Question 1?", "Question 2?"]
}}
"""

CLARIFICATION_PROMPT = """You are an AI assistant helping to complete a grievance form.

Current extracted data:
{current_data}

Missing information:
{missing_info}

User's response to clarification:
{user_response}

Update the extracted data based on the user's response. If new information fills in missing fields, update them.
If there are still missing critical fields, generate new clarification questions.

Critical fields that MUST be filled:
- title, category, full_description, and at least one location field (landmark, location_hint, or area_ward_name)

Respond ONLY with a valid JSON object containing:
{{
  "updated_fields": {{}},
  "still_missing": [],
  "new_questions": [],
  "is_complete": boolean
}}

Do not include any markdown, comments, or explanations. The JSON must be parseable without any extra text.
"""

FORM_COMPLETION_CHECK_PROMPT = """Analyze the following grievance form data and determine if it has enough information to be submitted.

Form Data:
{form_data}

Required fields: title, category, full_description, and at least one location field (landmark, location_hint, or area_ward_name)

Respond with JSON:
{{
  "is_complete": boolean,
  "missing_critical_fields": [],
  "suggested_questions": []
}}

Do not include any markdown, comments, or explanations. The JSON must be parseable without any extra text.
"""
