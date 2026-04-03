from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from services.nagpur_data_service.db.connection import get_nagpur_db
from google.cloud import firestore

router = APIRouter()

@router.get("/wards")
async def list_wards(zone_id: Optional[str] = None):
    """List all Nagpur wards, optionally filtered by zone."""
    db = get_nagpur_db()
    query = db.collection("wards")
    if zone_id:
        query = query.where("zone_id", "==", zone_id)
    
    docs = query.order_by("ward_number").stream()
    wards = []
    async for doc in docs:
        data = doc.to_dict()
        data["_id"] = doc.id
        wards.append(data)
    
    return {"wards": wards, "total": len(wards)}

@router.get("/zones")
async def list_zones():
    """List all Nagpur zones with ward counts via in-memory aggregation."""
    db = get_nagpur_db()
    docs = db.collection("wards").stream()
    
    zone_map = {}
    async for doc in docs:
        data = doc.to_dict()
        zid = data.get("zone_id")
        if not zid: continue
        
        if zid not in zone_map:
            zone_map[zid] = {
                "zone_id": zid,
                "zone_name": data.get("zone"),
                "ward_count": 0,
                "total_population": 0,
                "wards": []
            }
        
        zm = zone_map[zid]
        zm["ward_count"] += 1
        zm["total_population"] += data.get("population", 0)
        zm["wards"].append({
            "ward_id": doc.id,
            "ward_name": data.get("ward_name"),
            "ward_number": data.get("ward_number")
        })
    
    # Sort by zone_id
    sorted_zones = [zone_map[zid] for zid in sorted(zone_map.keys())]
    return {"zones": sorted_zones, "total": len(sorted_zones)}

@router.get("/wards/{ward_id}")
async def get_ward(ward_id: str):
    """Get details for a specific ward."""
    db = get_nagpur_db()
    doc = await db.collection("wards").document(ward_id).get()
    if not doc.exists:
        # Try finding by 'ward_id' field if it exists
        docs = db.collection("wards").where("ward_id", "==", ward_id).limit(1).stream()
        async for d in docs:
            data = d.to_dict()
            data["_id"] = d.id
            return data
        raise HTTPException(status_code=404, detail="Ward not found")
    
    data = doc.to_dict()
    data["_id"] = doc.id
    return data

@router.get("/wards/{ward_id}/stats")
async def get_ward_stats(ward_id: str):
    """Get complaint stats and civic data for a specific ward."""
    db = get_nagpur_db()
    
    # Get ward info
    doc = await db.collection("wards").document(ward_id).get()
    ward_data = None
    if doc.exists:
        ward_data = doc.to_dict()
    else:
        docs = db.collection("wards").where("ward_id", "==", ward_id).limit(1).stream()
        async for d in docs:
            ward_data = d.to_dict()
            ward_id = d.id # Normalize to doc ID
            break
            
    if not ward_data:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    # Get complaint stats from grievance_forms
    g_col = db.collection("grievance_forms")
    
    # Total
    total_snap = await g_col.where("ward_id", "==", ward_id).count().get()
    total = total_snap[0].value
    
    # Resolved/Closed
    resolved_snap = await g_col.where("ward_id", "==", ward_id)\
                               .where("status", "in", ["resolved", "closed", "confirmed", "Resolved"])\
                               .count().get()
    resolved = resolved_snap[0].value
    
    open_count = total - resolved

    # Top category via manual scan
    docs = g_col.where("ward_id", "==", ward_id).stream()
    cat_counts = {}
    async for d in docs:
        cat = d.to_dict().get("category")
        if cat:
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            
    top_cat = max(cat_counts, key=cat_counts.get) if cat_counts else None

    # Water/Sanitation data counts
    water_snap = await db.collection("water_supply_data").where("ward_id", "==", ward_id).count().get()
    sanitation_snap = await db.collection("sanitation_data").where("ward_id", "==", ward_id).count().get()

    return {
        "ward_id": ward_id,
        "ward_name": ward_data["ward_name"],
        "zone": ward_data["zone"],
        "population": ward_data.get("population"),
        "area_sq_km": ward_data.get("area_sq_km"),
        "total_complaints": total,
        "open_complaints": open_count,
        "resolved_complaints": resolved,
        "top_category": top_cat,
        "water_supply_records": water_snap[0].value,
        "sanitation_records": sanitation_snap[0].value,
    }
