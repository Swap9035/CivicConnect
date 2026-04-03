from fastapi import APIRouter, Query
from typing import Optional
from services.nagpur_data_service.db.connection import get_nagpur_db

router = APIRouter()

@router.get("/water-supply")
async def get_water_supply(
    ward_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    """Get water supply data, filterable by ward/zone."""
    db = get_nagpur_db()
    coll = db.collection("water_supply_data")
    
    query = coll
    if ward_id:
        query = query.where("ward_id", "==", ward_id)
    if zone_id:
        query = query.where("zone_id", "==", zone_id)
    
    total_snap = await query.count().get()
    total = total_snap[0].value
    
    records = []
    docs = query.offset(skip).limit(limit).stream()
    async for doc in docs:
        data = doc.to_dict()
        data["_id"] = doc.id
        records.append(data)
    
    return {"records": records, "total": total, "skip": skip, "limit": limit}

@router.get("/sanitation")
async def get_sanitation(
    ward_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    """Get sanitation data, filterable by ward/zone."""
    db = get_nagpur_db()
    coll = db.collection("sanitation_data")
    
    query = coll
    if ward_id:
        query = query.where("ward_id", "==", ward_id)
    if zone_id:
        query = query.where("zone_id", "==", zone_id)
    
    total_snap = await query.count().get()
    total = total_snap[0].value
    
    records = []
    docs = query.offset(skip).limit(limit).stream()
    async for doc in docs:
        data = doc.to_dict()
        data["_id"] = doc.id
        records.append(data)
    
    return {"records": records, "total": total, "skip": skip, "limit": limit}

@router.get("/civic-metrics")
async def get_civic_metrics(
    ward_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    """Get civic infrastructure metrics."""
    db = get_nagpur_db()
    coll = db.collection("civic_metrics")
    
    query = coll
    if ward_id:
        query = query.where("ward_id", "==", ward_id)
    if zone_id:
        query = query.where("zone_id", "==", zone_id)
    if category:
        query = query.where("metric_category", "==", category)
    
    total_snap = await query.count().get()
    total = total_snap[0].value
    
    records = []
    docs = query.offset(skip).limit(limit).stream()
    async for doc in docs:
        data = doc.to_dict()
        data["_id"] = doc.id
        records.append(data)
    
    return {"records": records, "total": total, "skip": skip, "limit": limit}

@router.get("/datasets/summary")
async def get_datasets_summary():
    """Get summary counts for all loaded datasets."""
    db = get_nagpur_db()
    
    water_snap = await db.collection("water_supply_data").count().get()
    sanitation_snap = await db.collection("sanitation_data").count().get()
    civic_snap = await db.collection("civic_metrics").count().get()
    ward_snap = await db.collection("wards").count().get()
    
    water_count = water_snap[0].value
    sanitation_count = sanitation_snap[0].value
    civic_count = civic_snap[0].value
    ward_count = ward_snap[0].value
    
    return {
        "wards_loaded": ward_count,
        "water_supply_records": water_count,
        "sanitation_records": sanitation_count,
        "civic_metric_records": civic_count,
        "total_dataset_records": water_count + sanitation_count + civic_count
    }
