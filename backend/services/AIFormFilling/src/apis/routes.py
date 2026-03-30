import uuid
from datetime import datetime
from typing import Optional, List
import os
import shutil
import json
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from bson import ObjectId

from ..db.connection import get_collection
from ..agents.form_extraction_agent import FormExtractionAgent
from shared.utils.auth_middleware import get_current_user
from ..utils.notifications import ai_notification_service
from services.user_service.src.db.connection import get_users_collection
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Grievance Form"])

# Temporary directory for storing uploaded files
TEMP_DIR = "./grievance_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

# Request/Response Models
class InitialSubmissionRequest(BaseModel):
    text: str

class ClarificationRequest(BaseModel):
    session_id: str
    user_response: Optional[str] = None
    answers: Optional[dict] = None

class FormSubmissionRequest(BaseModel):
    session_id: str
    confirmed: bool = True
    edits: Optional[dict] = None

class SessionResponse(BaseModel):
    session_id: str
    extracted_data: dict
    missing_info: List[str]
    clarification_questions: List[str]
    is_complete: bool
    message: str

class FormResponse(BaseModel):
    form_id: str
    status: str
    form_data: dict
    message: str

# Initialize agent
agent = FormExtractionAgent()

@router.post("/start", response_model=SessionResponse)
async def start_grievance_session(
    text: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    user_id: str = Depends(get_current_user)
):
    """
    Start a new grievance form session.
    The agent extracts structured data from the text and identifies missing information.
    Accepts text and optional file uploads.
    """
    sessions_collection = get_collection("form_sessions")
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Store uploaded files in temp directory
    document_paths = []
    if files:
        for file in files:
            if file.filename:
                file_path = os.path.join(TEMP_DIR, f"{session_id}_{file.filename}")
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                document_paths.append(file_path)
    
    # Build additional context from file paths (for agent)
    additional_context = ""
    if document_paths:
        additional_context = f"Attached files: {', '.join([os.path.basename(p) for p in document_paths])}"
    
    # Extract data using the agent
    extracted_data = await agent.extract_from_text(text, additional_context)
    
    # Check for errors
    if "error" in extracted_data:
        missing_info = extracted_data.get("missing_info", ["all fields"])
        clarification_questions = extracted_data.get("clarification_questions", [])
    else:
        missing_info = extracted_data.get("missing_info", [])
        clarification_questions = extracted_data.get("clarification_questions", [])
    
    # Determine if form is complete
    is_complete = len(missing_info) == 0 and "error" not in extracted_data
    
    # Create session document
    session_doc = {
        "session_id": session_id,
        "user_id": user_id,
        "original_text": text,
        "document_paths": document_paths,  # Store file paths instead of URLs
        "extracted_data": extracted_data,
        "missing_info": missing_info,
        "clarification_questions": clarification_questions,
        "conversation_history": [
            {"role": "user", "content": text, "timestamp": datetime.utcnow().isoformat()}
        ],
        "is_complete": is_complete,
        "final_form": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await sessions_collection.insert_one(session_doc)
    
    # Generate response message
    if is_complete:
        message = "I've drafted your grievance report. Please review and confirm the details."
    else:
        dept = extracted_data.get("category", "the relevant department")
        message = f"I've drafted your report for {dept}. "
        if clarification_questions:
            message += clarification_questions[0]
        elif missing_info:
            message += f"I need a bit more information: {', '.join(missing_info[:2])}"
    
    return SessionResponse(
        session_id=session_id,
        extracted_data=extracted_data,
        missing_info=missing_info,
        clarification_questions=clarification_questions,
        is_complete=is_complete,
        message=message
    )

@router.post("/clarify", response_model=SessionResponse)
async def provide_clarification(request: ClarificationRequest, user_id: str = Depends(get_current_user)):
    """
    Provide additional information to clarify missing fields.
    The agent updates the form based on the user's response.
    """
    sessions_collection = get_collection("form_sessions")
    
    # Get existing session
    session = await sessions_collection.find_one({"session_id": request.session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify session belongs to user
    if session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Build a string user_response for the agent:
    if request.user_response:
        user_response = request.user_response
        convo_content = request.user_response
    elif request.answers:
        # prefer structured answers; send JSON string to agent
        user_response = json.dumps(request.answers)
        convo_content = request.answers
    else:
        user_response = ""
        convo_content = ""
    
    # Process clarification with agent
    clarification_result = await agent.process_clarification(
        current_data=session["extracted_data"],
        missing_info=session["missing_info"],
        user_response=user_response
    )
    
    # Update extracted data with new fields
    updated_data = {**session["extracted_data"]}
    updated_fields = clarification_result.get("updated_fields", {})
    updated_data.update(updated_fields)
    
    # Update missing info and questions
    still_missing = clarification_result.get("still_missing", [])
    new_questions = clarification_result.get("new_questions", [])
    is_complete = clarification_result.get("is_complete", False)
    
    # If agent says complete, double-check
    if is_complete:
        completion_check = await agent.check_form_completion(updated_data)
        is_complete = completion_check.get("is_complete", False)
        if not is_complete:
            still_missing = completion_check.get("missing_critical_fields", [])
            new_questions = completion_check.get("suggested_questions", [])
    
    # Update conversation history
    conversation_history = session.get("conversation_history", [])
    conversation_history.append({
        "role": "user",
        "content": convo_content,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Update session in database
    await sessions_collection.update_one(
        {"session_id": request.session_id},
        {
            "$set": {
                "extracted_data": updated_data,
                "missing_info": still_missing,
                "clarification_questions": new_questions,
                "conversation_history": conversation_history,
                "is_complete": is_complete,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Generate response message
    if is_complete:
        message = "Great! Your grievance report is now complete. Please review and confirm."
    elif new_questions:
        message = new_questions[0]
    else:
        message = "Thank you for the information. Is there anything else you'd like to add?"
    
    return SessionResponse(
        session_id=request.session_id,
        extracted_data=updated_data,
        missing_info=still_missing,
        clarification_questions=new_questions,
        is_complete=is_complete,
        message=message
    )

@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, user_id: str = Depends(get_current_user)):
    """Get the current state of a grievance form session."""
    sessions_collection = get_collection("form_sessions")
    
    session = await sessions_collection.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify session belongs to user
    if session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return SessionResponse(
        session_id=session["session_id"],
        extracted_data=session["extracted_data"],
        missing_info=session["missing_info"],
        clarification_questions=session["clarification_questions"],
        is_complete=session["is_complete"],
        message="Session retrieved successfully"
    )

async def _fetch_user_email_by_id(user_id: str):
    """Find user's email in the userdb 'users' collection using the user_id (from auth middleware)."""
    if not user_id:
        return None

    try:
        users_col = get_users_collection()
    except Exception as e:
        logger.exception(f"Failed to get users collection: {e}")
        return None

    # Try common id-based queries; prefer querying by ObjectId if possible
    queries = []
    try:
        queries.append({"_id": ObjectId(user_id)})
    except Exception:
        pass
    queries.extend([{"user_id": user_id}, {"id": user_id}, {"sub": user_id}, {"mobile_number": user_id}])

    for q in queries:
        try:
            u = await users_col.find_one(q)
            if u:
                for f in ("email", "user_email", "email_primary", "emailAddress"):
                    if u.get(f):
                        return u.get(f)
        except Exception:
            continue

    return None

@router.post("/submit", response_model=FormResponse)
async def submit_grievance_form(request: FormSubmissionRequest, user_id: str = Depends(get_current_user)):
    """
    Submit the final grievance form after user confirmation.
    Allows optional edits before final submission.
    """
    sessions_collection = get_collection("form_sessions")
    forms_collection = get_collection("grievance_forms")
    
    # Get session
    session = await sessions_collection.find_one({"session_id": request.session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify session belongs to user
    if session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Prepare final form data
    form_data = {**session["extracted_data"]}
    
    # Remove agent metadata from form data
    form_data.pop("missing_info", None)
    form_data.pop("clarification_questions", None)
    form_data.pop("error", None)
    form_data.pop("raw_response", None)
    
    # Apply user edits if provided
    if request.edits:
        form_data.update(request.edits)
    
    # Generate form ID
    form_id = str(uuid.uuid4())
    
    # Create final form document
    final_form = {
        "form_id": form_id,
        "session_id": request.session_id,
        "user_id": user_id,
        "original_text": session["original_text"],
        "document_paths": session.get("document_paths", []),  # Store file paths
        **form_data,
        "status": "submitted",
        "created_at": datetime.utcnow(),
        "submitted_at": datetime.utcnow()
    }
    
    # Save to forms collection
    await forms_collection.insert_one(final_form)
    
    # Update session with final form reference
    await sessions_collection.update_one(
        {"session_id": request.session_id},
        {
            "$set": {
                "final_form": form_id,
                "is_complete": True,
                "updated_at": datetime.utcnow()
            }
        }
    )

    # Try to notify citizen by email with ticket id and summary
    citizen_email = form_data.get("email") or form_data.get("user_email")
    if not citizen_email:
        # attempt to fetch from user DB using user_id (session owner)
        try:
            found = await _fetch_user_email_by_id(user_id)
            if found:
                citizen_email = found
                logger.info(f"Found citizen email from userdb for user {user_id}")
            else:
                logger.warning(f"No citizen email found in form or userdb for form {form_id}; skipping notification")
        except Exception as e:
            logger.exception(f"Error while fetching citizen email from userdb for {form_id}: {e}")

    if citizen_email:
        try:
            sent = await ai_notification_service.send_ticket_email(
                to_email=citizen_email,
                form_id=form_id,
                form_data=form_data
            )
            if sent:
                logger.info(f"Submission notification sent to {citizen_email} for {form_id}")
            else:
                logger.error(f"Failed to send submission notification to {citizen_email} for {form_id}")
        except Exception as e:
            logger.exception(f"Error when sending submission notification for {form_id}: {e}")

    return FormResponse(
        form_id=form_id,
        status="submitted",
        form_data=form_data,
        message=f"Your grievance has been submitted successfully! Reference ID: {form_id}"
    )

@router.get("/form/{form_id}")
async def get_grievance_form(form_id: str, user_id: str = Depends(get_current_user)):
    """Get a submitted grievance form by ID."""
    forms_collection = get_collection("grievance_forms")
    
    form = await forms_collection.find_one({"form_id": form_id})
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Verify form belongs to user
    if form.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Remove MongoDB _id for JSON serialization
    form.pop("_id", None)
    
    return form

@router.get("/forms")
async def get_all_grievance_forms(user_id: str = Depends(get_current_user)):
    """Get all submitted grievance forms for the logged-in user."""
    forms_collection = get_collection("grievance_forms")
    
    # Retrieve all forms for the user
    forms = await forms_collection.find({"user_id": user_id}).to_list(length=None)
    
    # Remove MongoDB _id from each form for JSON serialization
    for form in forms:
        form.pop("_id", None)
    
    return forms

@router.get("/status/{form_id}")
async def get_grievance_status(form_id: str, user_id: str = Depends(get_current_user)):
    """Get the status and progress details for a specific grievance (normalized + citizen-friendly)."""
    forms_collection = get_collection("grievance_forms")
    
    form = await forms_collection.find_one({"form_id": form_id})
    if not form:
        raise HTTPException(status_code=404, detail="Grievance not found")
    
    # Verify form belongs to user
    if form.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Normalize status and infer steps
    raw_status = str(form.get("status", "submitted") or "submitted").strip()
    status_l = raw_status.lower()
    
    # If analysis timestamp exists but status still 'submitted' -> treat as analyzed
    if status_l in ("submitted", "pending") and form.get("analyzed_at"):
        status_l = "analyzed"
    
    # Map various stored values to canonical internal keys
    canonical_map = {
        "submitted": "submitted",
        "pending": "submitted",
        "analyzed": "analyzed",
        "analysis_complete": "analyzed",
        "assigned": "assigned",
        "linked": "assigned",
        "in progress": "in_progress",
        "in_progress": "in_progress",
        "working": "in_progress",
        "resolved": "resolved",
        "completed": "resolved",
        "closed": "resolved",
        "done": "resolved"
    }
    canonical = canonical_map.get(status_l, status_l)
    
    # Progress mapping aligned with frontend steps
    progress_map = {
        "submitted": 0,
        "analyzed": 1,
        "assigned": 2,
        "in_progress": 3,
        "resolved": 4
    }
    progress = progress_map.get(canonical, 0)
    
    # Human-friendly display labels
    display_labels = {
        "submitted": "Submitted",
        "analyzed": "Analyzed",
        "assigned": "Assigned",
        "in_progress": "In Progress",
        "resolved": "Resolved"
    }
    display_status = display_labels.get(canonical, raw_status.capitalize())
    
    # Citizen-friendly messages (fallback to stored message if present)
    messages = {
        "submitted": "Your grievance has been submitted and is awaiting analysis.",
        "analyzed": "Your grievance has been analyzed and is being routed for action.",
        "assigned": f"Assigned to {form.get('assigned_officer_name', 'an officer')} in {form.get('assigned_department', 'the department')}.",
        "in_progress": "An officer is actively working on your grievance.",
        "resolved": "Your grievance has been resolved. Please provide feedback if available."
    }
    message = form.get("message") or messages.get(canonical, "Status update in progress.")
    
    return {
        "form_id": form_id,
        "status": display_status,
        "raw_status": raw_status,
        "progress": progress,
        "message": message,
        "assigned_officer": form.get("assigned_officer_name"),
        "department": form.get("assigned_department"),
        "estimated_response_time": form.get("estimated_response_time"),
        "resolved_at": form.get("resolved_at")
    }
