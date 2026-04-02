from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from services.nagpur_data_service.db.connection import get_nagpur_db

router = APIRouter()


@router.get("/wards")
async def list_wards(zone_id: Optional[str] = None):
    """List all Nagpur wards, optionally filtered by zone."""
    db = get_nagpur_db()
    query = {}
    if zone_id:
        query["zone_id"] = zone_id
    
    wards = []
    async for ward in db.wards.find(query).sort("ward_number", 1):
        ward["_id"] = str(ward["_id"])
        wards.append(ward)
    
    return {"wards": wards, "total": len(wards)}


@router.get("/zones")
async def list_zones():
    """List all Nagpur zones with ward counts."""
    db = get_nagpur_db()
    pipeline = [
        {"$group": {
            "_id": "$zone_id",
            "zone_name": {"$first": "$zone"},
            "ward_count": {"$sum": 1},
            "total_population": {"$sum": {"$ifNull": ["$population", 0]}},
            "wards": {"$push": {"ward_id": "$_id", "ward_name": "$ward_name", "ward_number": "$ward_number"}}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    zones = []
    async for zone in db.wards.aggregate(pipeline):
        zone["zone_id"] = zone.pop("_id")
        zones.append(zone)
    
    return {"zones": zones, "total": len(zones)}


@router.get("/wards/{ward_id}")
async def get_ward(ward_id: str):
    """Get details for a specific ward."""
    db = get_nagpur_db()
    ward = await db.wards.find_one({"_id": ward_id})
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    ward["_id"] = str(ward["_id"])
    return ward


@router.get("/wards/{ward_id}/stats")
async def get_ward_stats(ward_id: str):
    """Get complaint stats and civic data for a specific ward."""
    db = get_nagpur_db()
    
    ward = await db.wards.find_one({"_id": ward_id})
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    # Get complaint stats from grievance_db
    from services.AIFormFilling.src.db.connection import get_database as get_grievance_db
    gdb = get_grievance_db()
    
    total = await gdb.grievance_forms.count_documents({"ward_id": ward_id})
    open_count = await gdb.grievance_forms.count_documents({
        "ward_id": ward_id,
        "status": {"$nin": ["resolved", "closed", "confirmed"]}
    })
    resolved = await gdb.grievance_forms.count_documents({
        "ward_id": ward_id,
        "status": {"$in": ["resolved", "closed", "confirmed"]}
    })

    # Top category
    cat_pipeline = [
        {"$match": {"ward_id": ward_id}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    top_cat = None
    async for doc in gdb.grievance_forms.aggregate(cat_pipeline):
        top_cat = doc["_id"]

    # Water supply data
    water_count = await db.water_supply_data.count_documents({"ward_id": ward_id})
    sanitation_count = await db.sanitation_data.count_documents({"ward_id": ward_id})

    return {
        "ward_id": ward_id,
        "ward_name": ward["ward_name"],
        "zone": ward["zone"],
        "population": ward.get("population"),
        "area_sq_km": ward.get("area_sq_km"),
        "total_complaints": total,
        "open_complaints": open_count,
        "resolved_complaints": resolved,
        "top_category": top_cat,
        "water_supply_records": water_count,
        "sanitation_records": sanitation_count,
    }
