from fastapi import APIRouter, BackgroundTasks, HTTPException
from datetime import datetime
from typing import Dict
import asyncio

from services.AIAnalysis.db import get_database as get_analysis_db, AnalysisRecord
from services.AIFormFilling.src.db.connection import get_database as get_grievance_db
from services.AIAnalysis.shared.schemas import GrievanceData, AnalysisResult
from services.AIAnalysis.agents import (
    VectorEmbeddingAgent,
    PriorityScorerAgent,
    SmartRoutingAgent,
    NotificationDispatcherAgent,
    DocumentAnalysisAgent
)

router = APIRouter()

# Initialize agents
vector_agent = VectorEmbeddingAgent()
priority_agent = PriorityScorerAgent()
routing_agent = SmartRoutingAgent()
notification_agent = NotificationDispatcherAgent()
document_agent = DocumentAnalysisAgent()

async def monitor_grievance_submissions():
    """
    Background worker that polls the grievance_forms collection every minute
    for new submissions with status 'submitted' and triggers analysis pipeline.
    """
    db = get_grievance_db()  # Synchronous call
    collection = db.grievance_forms
    
    while True:
        try:
            print("Polling for new grievances...")
            # Query for documents with status 'submitted'
            cursor = collection.find({"status": "submitted"})
            async for doc in cursor:
                print(f"Processing new grievance: {doc.get('form_id')}")
                
                # Extract GrievanceData from document
                grievance = GrievanceData(
                    form_id=doc['form_id'],
                    user_id=doc['user_id'],
                    title=doc['title'],
                    full_description=doc['full_description'],
                    category=doc['category'],
                    area_ward_name=doc['area_ward_name'],
                    impacted_population=doc['impacted_population'],
                    is_recurring=doc['is_recurring'],
                    document_paths=doc.get('document_paths', [])
                )
                
                # Run analysis pipeline
                await run_analysis_pipeline(grievance)
            
            # Wait for 60 seconds before next poll
            await asyncio.sleep(60)
            
        except Exception as e:
            print(f"Error in grievance monitoring: {e}")
            await asyncio.sleep(60)  # Wait before retrying

@router.get("/")
async def root():
    return {
        "service": "AI Analysis Service",
        "status": "running",
        "version": "1.0.0"
    }

@router.post("/analyze", response_model=Dict)
async def analyze_grievance(
    grievance: GrievanceData,
    background_tasks: BackgroundTasks
):
    """
    Main endpoint to trigger the analysis pipeline.
    Called by AIFormFilling service after form submission.
    """
    try:
        # Run analysis in background
        background_tasks.add_task(
            run_analysis_pipeline,
            grievance
        )
        
        return {
            "status": "accepted",
            "message": "Analysis pipeline initiated",
            "form_id": grievance.form_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_analysis_pipeline(grievance: GrievanceData):
    """
    Execute the four-module analysis pipeline
    """
    try:
        # Module A: Vector Embedding & Duplicate Check
        print(f"[A] Checking for duplicates: {grievance.form_id}")
        vector_check = await vector_agent.check_duplicate(grievance)
        
        # Module B: Priority Scorer
        print(f"[B] Scoring priority: {grievance.form_id}")
        priority_score = await priority_agent.score_priority(grievance)
        
        # Module C: Smart Routing
        print(f"[C] Routing to department: {grievance.form_id}")
        routing = await routing_agent.route_grievance(
            grievance, 
            priority_score.urgency_level
        )
        
        # Determine final status
        if vector_check.is_duplicate:
            status = "Linked"
        else:
            status = "Assigned"
        
        # Module D: Document Analysis
        print(f"[D] Analyzing documents: {grievance.form_id}")
        document_insights = await document_agent.analyze_documents(grievance.document_paths)
        
        # Create analysis result
        analysis_result = AnalysisResult(
            form_id=grievance.form_id,
            vector_check=vector_check,
            priority_score=priority_score,
            routing=routing,
            status=status,
            analyzed_at=datetime.utcnow(),
            document_insights=document_insights
        )
        
        # Module E: Notification Dispatch
        print(f"[E] Dispatching notifications: {grievance.form_id}")
        await notification_agent.dispatch_notifications(analysis_result)
        
        # Create citizen message for DB storage
        if analysis_result.vector_check.is_duplicate:
            citizen_message = (
                f"Your grievance #{analysis_result.form_id} has been linked to an existing case "
                f"#{analysis_result.vector_check.parent_form_id}. You'll receive updates on the resolution."
            )
        else:
            citizen_message = (
                f"Your grievance #{analysis_result.form_id} has been assigned to "
                f"{analysis_result.routing.officer_name} ({analysis_result.routing.department}). "
                f"Expected response time: {analysis_result.routing.estimated_response_time}."
            )
        
        # Store analysis record in database
        await save_analysis_record(grievance, analysis_result)
        
        # Update grievance form status in AIFormFilling database
        await update_grievance_status(grievance.form_id, status, analysis_result, citizen_message)
        
        print(f"✅ Analysis pipeline completed for {grievance.form_id}")
        
    except Exception as e:
        print(f"❌ Error in analysis pipeline for {grievance.form_id}: {e}")
        # Log error but don't raise to avoid breaking background task

async def save_analysis_record(grievance: GrievanceData, analysis: AnalysisResult):
    """Save analysis record to database"""
    db = get_analysis_db()  # Synchronous call
    
    record = AnalysisRecord(
        form_id=analysis.form_id,
        user_id=grievance.user_id,
        is_duplicate=analysis.vector_check.is_duplicate,
        parent_form_id=analysis.vector_check.parent_form_id,
        similarity_score=analysis.vector_check.similarity_score,
        priority_score=analysis.priority_score.score,
        priority_reasoning=analysis.priority_score.reasoning,
        urgency_level=analysis.priority_score.urgency_level,
        assigned_department=analysis.routing.department,
        assigned_officer_id=analysis.routing.officer_id,
        assigned_officer_name=analysis.routing.officer_name,
        estimated_response_time=analysis.routing.estimated_response_time,
        status=analysis.status,
        analyzed_at=analysis.analyzed_at
    )
    
    await db.analysis_records.insert_one(record.model_dump())

async def update_grievance_status(
    form_id: str, 
    status: str, 
    analysis: AnalysisResult,
    citizen_message: str
):
    """Update grievance form in AIFormFilling database"""
    db = get_grievance_db()  # Synchronous call
    
    update_data = {
        "status": status,  # Changed to use the passed status ("assigned" or "linked")
        "analyzed_at": analysis.analyzed_at,
        "priority_score": analysis.priority_score.score,
        "priority_reasoning": analysis.priority_score.reasoning,  # Added for citizen info
        "urgency_level": analysis.priority_score.urgency_level,
        "assigned_department": analysis.routing.department,
        "assigned_officer_id": analysis.routing.officer_id,
        "assigned_officer_name": analysis.routing.officer_name,
        "estimated_response_time": analysis.routing.estimated_response_time,
        "message": citizen_message,  # Added message field
        "document_insights": analysis.document_insights  # Added for citizen info
    }
    
    if analysis.vector_check.is_duplicate:
        update_data["parent_form_id"] = analysis.vector_check.parent_form_id
        update_data["similarity_score"] = analysis.vector_check.similarity_score  # Added for citizen info
    
    await db.grievance_forms.update_one(
        {"form_id": form_id},
        {"$set": update_data}
    )

@router.get("/analysis/{form_id}")
async def get_analysis(form_id: str):
    """Retrieve analysis record for a form"""
    db = get_analysis_db()  # Synchronous call
    
    record = await db.analysis_records.find_one({"form_id": form_id})
    
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found")
    
    record["_id"] = str(record["_id"])
    return record

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AIAnalysis"}
