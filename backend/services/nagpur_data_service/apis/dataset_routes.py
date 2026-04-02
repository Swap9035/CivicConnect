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
    query = {}
    if ward_id:
        query["ward_id"] = ward_id
    if zone_id:
        query["zone_id"] = zone_id
    
    total = await db.water_supply_data.count_documents(query)
    records = []
    async for doc in db.water_supply_data.find(query).skip(skip).limit(limit):
        doc["_id"] = str(doc["_id"])
        records.append(doc)
    
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
    query = {}
    if ward_id:
        query["ward_id"] = ward_id
    if zone_id:
        query["zone_id"] = zone_id
    
    total = await db.sanitation_data.count_documents(query)
    records = []
    async for doc in db.sanitation_data.find(query).skip(skip).limit(limit):
        doc["_id"] = str(doc["_id"])
        records.append(doc)
    
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
    query = {}
    if ward_id:
        query["ward_id"] = ward_id
    if zone_id:
        query["zone_id"] = zone_id
    if category:
        query["metric_category"] = category
    
    total = await db.civic_metrics.count_documents(query)
    records = []
    async for doc in db.civic_metrics.find(query).skip(skip).limit(limit):
        doc["_id"] = str(doc["_id"])
        records.append(doc)
    
    return {"records": records, "total": total, "skip": skip, "limit": limit}


@router.get("/datasets/summary")
async def get_datasets_summary():
    """Get summary counts for all loaded datasets."""
    db = get_nagpur_db()
    
    water_count = await db.water_supply_data.count_documents({})
    sanitation_count = await db.sanitation_data.count_documents({})
    civic_count = await db.civic_metrics.count_documents({})
    ward_count = await db.wards.count_documents({})
    
    return {
        "wards_loaded": ward_count,
        "water_supply_records": water_count,
        "sanitation_records": sanitation_count,
        "civic_metric_records": civic_count,
        "total_dataset_records": water_count + sanitation_count + civic_count
    }
