from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta
from services.nagpur_data_service.db.connection import get_nagpur_db

router = APIRouter()


@router.get("/heatmap")
async def get_heatmap_data():
    """Complaint density per ward for heatmap visualization."""
    db = get_nagpur_db()
    
    # Get complaint counts per ward from grievance DB
    from services.AIFormFilling.src.db.connection import get_database as get_grievance_db
    gdb = get_grievance_db()
    
    pipeline = [
        {"$match": {"ward_id": {"$ne": None, "$exists": True}}},
        {"$group": {"_id": "$ward_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    ward_counts = {}
    max_count = 1
    async for doc in gdb.grievance_forms.aggregate(pipeline):
        ward_counts[doc["_id"]] = doc["count"]
        if doc["count"] > max_count:
            max_count = doc["count"]

    # Merge with ward info
    heatmap_data = []
    async for ward in db.wards.find({}).sort("ward_number", 1):
        wid = ward["_id"]
        count = ward_counts.get(wid, 0)
        heatmap_data.append({
            "ward_id": wid,
            "ward_name": ward["ward_name"],
            "ward_number": ward["ward_number"],
            "zone": ward["zone"],
            "zone_id": ward["zone_id"],
            "count": count,
            "intensity": round(count / max_count, 2) if max_count > 0 else 0,
            "population": ward.get("population", 0),
        })

    return {"heatmap": heatmap_data, "max_count": max_count, "total_wards": len(heatmap_data)}


@router.get("/rankings")
async def get_ward_rankings(
    sort_by: str = Query("complaints", regex="^(complaints|resolution_time)$"),
    limit: int = Query(38, ge=1, le=38),
    order: str = Query("desc", regex="^(asc|desc)$")
):
    """Rank wards by complaint volume or avg resolution time."""
    from services.AIFormFilling.src.db.connection import get_database as get_grievance_db
    gdb = get_grievance_db()
    db = get_nagpur_db()

    pipeline = [
        {"$match": {"ward_id": {"$ne": None, "$exists": True}}},
        {"$group": {
            "_id": "$ward_id",
            "complaint_count": {"$sum": 1},
            "open_count": {"$sum": {"$cond": [{"$in": ["$status", ["submitted", "assigned", "in_progress", "Assigned", "In Progress"]]}, 1, 0]}},
            "resolved_count": {"$sum": {"$cond": [{"$in": ["$status", ["resolved", "closed", "confirmed", "Resolved"]]}, 1, 0]}},
            "categories": {"$push": "$category"},
        }},
        {"$sort": {"complaint_count": -1 if order == "desc" else 1}},
        {"$limit": limit}
    ]

    ward_stats = {}
    async for doc in gdb.grievance_forms.aggregate(pipeline):
        # Find top category
        cats = [c for c in doc.get("categories", []) if c]
        top_cat = max(set(cats), key=cats.count) if cats else None
        ward_stats[doc["_id"]] = {
            "complaint_count": doc["complaint_count"],
            "open_count": doc["open_count"],
            "resolved_count": doc["resolved_count"],
            "top_category": top_cat,
        }

    # Merge with ward info
    rankings = []
    async for ward in db.wards.find({}):
        wid = ward["_id"]
        stats = ward_stats.get(wid, {"complaint_count": 0, "open_count": 0, "resolved_count": 0, "top_category": None})
        rankings.append({
            "ward_id": wid,
            "ward_name": ward["ward_name"],
            "ward_number": ward["ward_number"],
            "zone": ward["zone"],
            "population": ward.get("population", 0),
            **stats
        })

    # Sort
    reverse = order == "desc"
    if sort_by == "complaints":
        rankings.sort(key=lambda x: x["complaint_count"], reverse=reverse)
    
    # Add rank numbers
    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    return {"rankings": rankings[:limit], "total": len(rankings), "sort_by": sort_by, "order": order}


@router.get("/trends")
async def get_complaint_trends(
    ward_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    days: int = Query(90, ge=7, le=365),
    group_by: str = Query("week", regex="^(day|week|month)$")
):
    """Time-series complaint trends, optionally filtered by ward/zone."""
    from services.AIFormFilling.src.db.connection import get_database as get_grievance_db
    gdb = get_grievance_db()

    start_date = datetime.utcnow() - timedelta(days=days)
    
    match_stage = {"created_at": {"$gte": start_date}}
    if ward_id:
        match_stage["ward_id"] = ward_id
    if zone_id:
        match_stage["zone_id"] = zone_id

    if group_by == "day":
        date_format = "%Y-%m-%d"
    elif group_by == "week":
        date_format = "%Y-W%V"
    else:
        date_format = "%Y-%m"

    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": {
                "period": {"$dateToString": {"format": date_format, "date": "$created_at"}},
                "category": "$category"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.period": 1}}
    ]

    # Collect by period and category
    trend_map = {}
    categories_set = set()
    async for doc in gdb.grievance_forms.aggregate(pipeline):
        period = doc["_id"]["period"]
        category = doc["_id"].get("category") or "Unknown"
        categories_set.add(category)
        if period not in trend_map:
            trend_map[period] = {"period": period}
        trend_map[period][category] = doc["count"]
        trend_map[period]["total"] = trend_map[period].get("total", 0) + doc["count"]

    # Also get total per period (no category split)
    total_pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": {"$dateToString": {"format": date_format, "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]

    totals = []
    async for doc in gdb.grievance_forms.aggregate(total_pipeline):
        totals.append({"period": doc["_id"], "count": doc["count"]})

    return {
        "trends": list(trend_map.values()),
        "totals": totals,
        "categories": sorted(categories_set),
        "days": days,
        "group_by": group_by,
    }


@router.get("/category-distribution")
async def get_category_distribution(ward_id: Optional[str] = None, zone_id: Optional[str] = None):
    """Distribution of complaints by category."""
    from services.AIFormFilling.src.db.connection import get_database as get_grievance_db
    gdb = get_grievance_db()

    match_stage = {}
    if ward_id:
        match_stage["ward_id"] = ward_id
    if zone_id:
        match_stage["zone_id"] = zone_id

    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]

    distribution = []
    total = 0
    async for doc in gdb.grievance_forms.aggregate(pipeline):
        cat = doc["_id"] or "Unknown"
        distribution.append({"category": cat, "count": doc["count"]})
        total += doc["count"]

    # Add percentages
    for d in distribution:
        d["percentage"] = round((d["count"] / total * 100), 1) if total > 0 else 0

    return {"distribution": distribution, "total": total}


@router.get("/zone-summary")
async def get_zone_summary():
    """Aggregate complaint stats per zone."""
    from services.AIFormFilling.src.db.connection import get_database as get_grievance_db
    gdb = get_grievance_db()
    db = get_nagpur_db()

    pipeline = [
        {"$match": {"zone_id": {"$ne": None, "$exists": True}}},
        {"$group": {
            "_id": "$zone_id",
            "complaint_count": {"$sum": 1},
            "open_count": {"$sum": {"$cond": [{"$in": ["$status", ["submitted", "assigned", "in_progress", "Assigned"]]}, 1, 0]}},
            "resolved_count": {"$sum": {"$cond": [{"$in": ["$status", ["resolved", "closed", "confirmed", "Resolved"]]}, 1, 0]}},
        }},
        {"$sort": {"complaint_count": -1}}
    ]

    zone_complaints = {}
    async for doc in gdb.grievance_forms.aggregate(pipeline):
        zone_complaints[doc["_id"]] = doc

    # Get zone info
    zone_pipeline = [
        {"$group": {
            "_id": "$zone_id",
            "zone_name": {"$first": "$zone"},
            "ward_count": {"$sum": 1},
            "total_population": {"$sum": {"$ifNull": ["$population", 0]}},
        }},
        {"$sort": {"_id": 1}}
    ]

    zones = []
    async for zone in db.wards.aggregate(zone_pipeline):
        zid = zone["_id"]
        stats = zone_complaints.get(zid, {"complaint_count": 0, "open_count": 0, "resolved_count": 0})
        zones.append({
            "zone_id": zid,
            "zone_name": zone["zone_name"],
            "ward_count": zone["ward_count"],
            "total_population": zone["total_population"],
            "complaint_count": stats.get("complaint_count", 0),
            "open_count": stats.get("open_count", 0),
            "resolved_count": stats.get("resolved_count", 0),
        })

    return {"zones": zones}


@router.get("/correlations")
async def get_correlations():
    """Cross-dataset correlation: water supply hours vs complaint count per ward."""
    from services.AIFormFilling.src.db.connection import get_database as get_grievance_db
    gdb = get_grievance_db()
    db = get_nagpur_db()

    # Complaint counts per ward
    complaint_pipeline = [
        {"$match": {"ward_id": {"$ne": None}}},
        {"$group": {"_id": "$ward_id", "complaint_count": {"$sum": 1}}}
    ]
    ward_complaints = {}
    async for doc in gdb.grievance_forms.aggregate(complaint_pipeline):
        ward_complaints[doc["_id"]] = doc["complaint_count"]

    # Water supply avg hours per ward
    water_pipeline = [
        {"$match": {"ward_id": {"$ne": None}, "supply_hours_per_day": {"$ne": None}}},
        {"$group": {"_id": "$ward_id", "avg_supply_hours": {"$avg": "$supply_hours_per_day"}}}
    ]
    ward_water = {}
    async for doc in db.water_supply_data.aggregate(water_pipeline):
        ward_water[doc["_id"]] = round(doc["avg_supply_hours"], 1)

    # Sanitation scores per ward
    sanitation_pipeline = [
        {"$match": {"ward_id": {"$ne": None}, "swachh_bharat_score": {"$ne": None}}},
        {"$group": {"_id": "$ward_id", "avg_sanitation_score": {"$avg": "$swachh_bharat_score"}}}
    ]
    ward_sanitation = {}
    async for doc in db.sanitation_data.aggregate(sanitation_pipeline):
        ward_sanitation[doc["_id"]] = round(doc["avg_sanitation_score"], 1)

    # Build scatter data
    scatter_data = []
    async for ward in db.wards.find({}):
        wid = ward["_id"]
        scatter_data.append({
            "ward_id": wid,
            "ward_name": ward["ward_name"],
            "complaint_count": ward_complaints.get(wid, 0),
            "avg_water_supply_hours": ward_water.get(wid),
            "avg_sanitation_score": ward_sanitation.get(wid),
            "population": ward.get("population", 0),
        })

    return {"scatter_data": scatter_data}


@router.get("/overview")
async def get_analytics_overview():
    """High-level overview stats for the analytics dashboard."""
    from services.AIFormFilling.src.db.connection import get_database as get_grievance_db
    gdb = get_grievance_db()
    db = get_nagpur_db()

    total_complaints = await gdb.grievance_forms.count_documents({})
    open_complaints = await gdb.grievance_forms.count_documents({
        "status": {"$in": ["submitted", "assigned", "in_progress", "Assigned", "In Progress", "draft"]}
    })
    resolved_complaints = await gdb.grievance_forms.count_documents({
        "status": {"$in": ["resolved", "closed", "confirmed", "Resolved"]}
    })
    total_wards = await db.wards.count_documents({})
    water_records = await db.water_supply_data.count_documents({})
    sanitation_records = await db.sanitation_data.count_documents({})

    # Most complained ward
    worst_ward_pipeline = [
        {"$match": {"ward_id": {"$ne": None}}},
        {"$group": {"_id": "$ward_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    worst_ward = None
    async for doc in gdb.grievance_forms.aggregate(worst_ward_pipeline):
        ward_info = await db.wards.find_one({"_id": doc["_id"]})
        if ward_info:
            worst_ward = {"ward_id": doc["_id"], "ward_name": ward_info["ward_name"], "count": doc["count"]}

    return {
        "total_complaints": total_complaints,
        "open_complaints": open_complaints,
        "resolved_complaints": resolved_complaints,
        "resolution_rate": round(resolved_complaints / max(total_complaints, 1) * 100, 1),
        "total_wards": total_wards,
        "water_supply_records": water_records,
        "sanitation_records": sanitation_records,
        "worst_ward": worst_ward,
    }


@router.get("/dataset-insights")
async def get_dataset_insights():
    """Aggregate imported CSV dataset records by zone/ward for visualization.
    This shows data even when no complaints have been submitted."""
    db = get_nagpur_db()

    # Sanitation records per zone
    san_zone_pipeline = [
        {"$match": {"zone_id": {"$ne": None}}},
        {"$group": {
            "_id": "$zone_id",
            "record_count": {"$sum": 1},
        }},
        {"$sort": {"record_count": -1}}
    ]
    sanitation_by_zone = []
    async for doc in db.sanitation_data.aggregate(san_zone_pipeline):
        sanitation_by_zone.append({"zone_id": doc["_id"], "record_count": doc["record_count"]})

    # Sanitation records per ward
    san_ward_pipeline = [
        {"$match": {"ward_id": {"$ne": None}}},
        {"$group": {
            "_id": "$ward_id",
            "record_count": {"$sum": 1},
        }},
        {"$sort": {"record_count": -1}}
    ]
    sanitation_by_ward = {}
    async for doc in db.sanitation_data.aggregate(san_ward_pipeline):
        sanitation_by_ward[doc["_id"]] = doc["record_count"]

    # Civic metrics per zone
    civic_zone_pipeline = [
        {"$match": {"zone_id": {"$ne": None}}},
        {"$group": {
            "_id": "$zone_id",
            "record_count": {"$sum": 1},
        }},
        {"$sort": {"record_count": -1}}
    ]
    civic_by_zone = []
    async for doc in db.civic_metrics.aggregate(civic_zone_pipeline):
        civic_by_zone.append({"zone_id": doc["_id"], "record_count": doc["record_count"]})

    # Water supply per zone
    water_zone_pipeline = [
        {"$match": {"zone_id": {"$ne": None}}},
        {"$group": {
            "_id": "$zone_id",
            "record_count": {"$sum": 1},
        }},
        {"$sort": {"record_count": -1}}
    ]
    water_by_zone = []
    async for doc in db.water_supply_data.aggregate(water_zone_pipeline):
        water_by_zone.append({"zone_id": doc["_id"], "record_count": doc["record_count"]})

    # Ward-level dataset records for heatmap
    ward_dataset_counts = {}
    for collection_name in ["sanitation_data", "water_supply_data", "civic_metrics"]:
        pipeline = [
            {"$match": {"ward_id": {"$ne": None}}},
            {"$group": {"_id": "$ward_id", "count": {"$sum": 1}}}
        ]
        async for doc in db[collection_name].aggregate(pipeline):
            wid = doc["_id"]
            ward_dataset_counts[wid] = ward_dataset_counts.get(wid, 0) + doc["count"]

    # Build ward dataset heatmap with ward info
    max_count = max(ward_dataset_counts.values()) if ward_dataset_counts else 1
    ward_dataset_heatmap = []
    async for ward in db.wards.find({}).sort("ward_number", 1):
        wid = ward["_id"]
        count = ward_dataset_counts.get(wid, 0)
        ward_dataset_heatmap.append({
            "ward_id": wid,
            "ward_name": ward["ward_name"],
            "ward_number": ward["ward_number"],
            "zone": ward["zone"],
            "zone_id": ward["zone_id"],
            "dataset_records": count,
            "intensity": round(count / max(max_count, 1), 2),
            "population": ward.get("population", 0),
        })

    # Zone-level summary with dataset counts
    zone_lookup = {}
    async for ward in db.wards.aggregate([
        {"$group": {"_id": "$zone_id", "zone_name": {"$first": "$zone"}, "ward_count": {"$sum": 1}}}
    ]):
        zone_lookup[ward["_id"]] = ward["zone_name"]

    zone_dataset_summary = []
    # Merge all collections per zone
    all_zone_ids = set()
    zone_totals = {}
    for collection_name in ["sanitation_data", "water_supply_data", "civic_metrics"]:
        async for doc in db[collection_name].aggregate([
            {"$match": {"zone_id": {"$ne": None}}},
            {"$group": {"_id": "$zone_id", "count": {"$sum": 1}}}
        ]):
            zid = doc["_id"]
            all_zone_ids.add(zid)
            if zid not in zone_totals:
                zone_totals[zid] = {"sanitation": 0, "water": 0, "civic": 0, "total": 0}
            if collection_name == "sanitation_data":
                zone_totals[zid]["sanitation"] = doc["count"]
            elif collection_name == "water_supply_data":
                zone_totals[zid]["water"] = doc["count"]
            else:
                zone_totals[zid]["civic"] = doc["count"]
            zone_totals[zid]["total"] += doc["count"]

    for zid in sorted(all_zone_ids):
        t = zone_totals.get(zid, {})
        zone_dataset_summary.append({
            "zone_id": zid,
            "zone_name": zone_lookup.get(zid, zid),
            "sanitation_records": t.get("sanitation", 0),
            "water_records": t.get("water", 0),
            "civic_records": t.get("civic", 0),
            "total_records": t.get("total", 0),
        })

    return {
        "sanitation_by_zone": sanitation_by_zone,
        "civic_by_zone": civic_by_zone,
        "water_by_zone": water_by_zone,
        "ward_dataset_heatmap": ward_dataset_heatmap,
        "zone_dataset_summary": zone_dataset_summary,
        "total_sanitation": await db.sanitation_data.count_documents({}),
        "total_water": await db.water_supply_data.count_documents({}),
        "total_civic": await db.civic_metrics.count_documents({}),
    }
