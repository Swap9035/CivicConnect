from fastapi import APIRouter, Query
from typing import Optional, List, Dict
from datetime import datetime, timedelta, timezone
from services.nagpur_data_service.db.connection import get_nagpur_db

router = APIRouter()

@router.get("/heatmap")
async def get_heatmap_data():
    """Complaint density per ward for heatmap visualization."""
    db = get_nagpur_db()
    g_col = db.collection("grievance_forms")
    w_col = db.collection("wards")
    
    # Get grievance counts per ward
    ward_counts = {}
    max_count = 1
    docs = g_col.where("ward_id", "!=", None).stream()
    async for doc in docs:
        wid = doc.to_dict().get("ward_id")
        if wid:
            ward_counts[wid] = ward_counts.get(wid, 0) + 1
            if ward_counts[wid] > max_count:
                max_count = ward_counts[wid]

    # Merge with ward info
    heatmap_data = []
    wdocs = w_col.order_by("ward_number").stream()
    async for wdoc in wdocs:
        ward = wdoc.to_dict()
        wid = wdoc.id
        count = ward_counts.get(wid, 0)
        heatmap_data.append({
            "ward_id": wid,
            "ward_name": ward.get("ward_name"),
            "ward_number": ward.get("ward_number"),
            "zone": ward.get("zone"),
            "zone_id": ward.get("zone_id"),
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
    """Rank wards by complaint volume via in-memory aggregation."""
    db = get_nagpur_db()
    g_col = db.collection("grievance_forms")
    w_col = db.collection("wards")

    # Aggregate stats in memory
    ward_stats = {}
    docs = g_col.stream()
    async for doc in docs:
        data = doc.to_dict()
        wid = data.get("ward_id")
        if not wid: continue
        
        if wid not in ward_stats:
            ward_stats[wid] = {
                "complaint_count": 0,
                "open_count": 0,
                "resolved_count": 0,
                "categories": []
            }
        
        stats = ward_stats[wid]
        stats["complaint_count"] += 1
        status = (data.get("status") or "").lower()
        if status in ["submitted", "assigned", "in_progress", "assigned", "in progress"]:
            stats["open_count"] += 1
        elif status in ["resolved", "closed", "confirmed", "resolved"]:
            stats["resolved_count"] += 1
        
        if data.get("category"):
            stats["categories"].append(data["category"])

    # Merge with ward info
    rankings = []
    wdocs = w_col.stream()
    async for wdoc in wdocs:
        ward = wdoc.to_dict()
        wid = wdoc.id
        s = ward_stats.get(wid, {"complaint_count": 0, "open_count": 0, "resolved_count": 0, "categories": []})
        
        # Calculate top category
        cats = s["categories"]
        top_cat = max(set(cats), key=cats.count) if cats else None
        
        rankings.append({
            "ward_id": wid,
            "ward_name": ward.get("ward_name"),
            "ward_number": ward.get("ward_number"),
            "zone": ward.get("zone"),
            "population": ward.get("population", 0),
            "complaint_count": s["complaint_count"],
            "open_count": s["open_count"],
            "resolved_count": s["resolved_count"],
            "top_category": top_cat,
        })

    # Sort
    reverse = order == "desc"
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
    """Time-series complaint trends via in-memory grouping."""
    db = get_nagpur_db()
    g_col = db.collection("grievance_forms")
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    query = g_col.where("created_at", ">=", start_date)
    if ward_id:
        query = query.where("ward_id", "==", ward_id)
    if zone_id:
        query = query.where("zone_id", "==", zone_id)

    trend_map = {}
    categories_set = set()
    docs = query.stream()
    
    async for doc in docs:
        data = doc.to_dict()
        dt = data.get("created_at")
        if not dt: continue
        
        # Format date for grouping
        if group_by == "day":
            period = dt.strftime("%Y-%m-%d")
        elif group_by == "week":
            period = dt.strftime("%Y-W%V")
        else:
            period = dt.strftime("%Y-%m")
            
        category = data.get("category") or "Unknown"
        categories_set.add(category)
        
        if period not in trend_map:
            trend_map[period] = {"period": period, "total": 0}
        
        trend_map[period][category] = trend_map[period].get(category, 0) + 1
        trend_map[period]["total"] += 1

    # Format for response
    sorted_periods = sorted(trend_map.keys())
    trends = [trend_map[p] for p in sorted_periods]
    
    totals = [{"period": p, "count": trend_map[p]["total"]} for p in sorted_periods]

    return {
        "trends": trends,
        "totals": totals,
        "categories": sorted(categories_set),
        "days": days,
        "group_by": group_by,
    }

@router.get("/category-distribution")
async def get_category_distribution(ward_id: Optional[str] = None, zone_id: Optional[str] = None):
    """Distribution of complaints by category via in-memory count."""
    db = get_nagpur_db()
    query = db.collection("grievance_forms")
    if ward_id:
        query = query.where("ward_id", "==", ward_id)
    if zone_id:
        query = query.where("zone_id", "==", zone_id)

    cat_counts = {}
    total = 0
    docs = query.stream()
    async for doc in docs:
        cat = doc.to_dict().get("category") or "Unknown"
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        total += 1

    distribution = []
    for cat, count in cat_counts.items():
        distribution.append({
            "category": cat,
            "count": count,
            "percentage": round((count / total * 100), 1) if total > 0 else 0
        })
    
    distribution.sort(key=lambda x: x["count"], reverse=True)
    return {"distribution": distribution, "total": total}

@router.get("/zone-summary")
async def get_zone_summary():
    """Aggregate complaint stats per zone via in-memory joining."""
    db = get_nagpur_db()
    
    # 1. Get zone info from wards
    zone_info = {}
    wdocs = db.collection("wards").stream()
    async for wdoc in wdocs:
        data = wdoc.to_dict()
        zid = data.get("zone_id")
        if not zid: continue
        if zid not in zone_info:
            zone_info[zid] = {
                "zone_id": zid,
                "zone_name": data.get("zone"),
                "ward_count": 0,
                "total_population": 0,
                "complaint_count": 0,
                "open_count": 0,
                "resolved_count": 0
            }
        zi = zone_info[zid]
        zi["ward_count"] += 1
        zi["total_population"] += data.get("population", 0)

    # 2. Get complaint stats from grievance_forms
    gdocs = db.collection("grievance_forms").stream()
    async for gdoc in gdocs:
        data = gdoc.to_dict()
        # Prefer zone_id on grievance; fallback to deriving from ward_id if we have it?
        # For simplicity, we use zone_id field
        zid = data.get("zone_id")
        if zid and zid in zone_info:
            zi = zone_info[zid]
            zi["complaint_count"] += 1
            status = (data.get("status") or "").lower()
            if status in ["submitted", "assigned", "in_progress", "assigned", "in progress"]:
                zi["open_count"] += 1
            elif status in ["resolved", "closed", "confirmed", "resolved"]:
                zi["resolved_count"] += 1

    return {"zones": list(zone_info.values())}

@router.get("/correlations")
async def get_correlations():
    """Cross-dataset correlation via in-memory ward-joining."""
    db = get_nagpur_db()
    
    # We'll map all data by ward_id
    ward_map = {}
    
    # Wards
    wdocs = db.collection("wards").stream()
    async for wdoc in wdocs:
        data = wdoc.to_dict()
        ward_map[wdoc.id] = {
            "ward_id": wdoc.id,
            "ward_name": data.get("ward_name"),
            "population": data.get("population", 0),
            "complaint_count": 0,
            "avg_water_supply_hours": None,
            "avg_sanitation_score": None
        }

    # Complaints
    gdocs = db.collection("grievance_forms").stream()
    async for gdoc in gdocs:
        wid = gdoc.to_dict().get("ward_id")
        if wid in ward_map:
            ward_map[wid]["complaint_count"] += 1

    # Water
    w_snap = db.collection("water_supply_data").stream()
    # Need to average manually
    water_sums = {}
    async for doc in w_snap:
        data = doc.to_dict()
        wid = data.get("ward_id")
        val = data.get("supply_hours_per_day")
        if wid and val is not None:
            if wid not in water_sums: water_sums[wid] = []
            water_sums[wid].append(val)
    for wid, vals in water_sums.items():
        if wid in ward_map:
            ward_map[wid]["avg_water_supply_hours"] = round(sum(vals) / len(vals), 1)

    # Sanitation
    s_snap = db.collection("sanitation_data").stream()
    san_sums = {}
    async for doc in s_snap:
        data = doc.to_dict()
        wid = data.get("ward_id")
        score = data.get("swachh_bharat_score")
        if wid and score is not None:
            if wid not in san_sums: san_sums[wid] = []
            san_sums[wid].append(score)
    for wid, vals in san_sums.items():
        if wid in ward_map:
            ward_map[wid]["avg_sanitation_score"] = round(sum(vals) / len(vals), 1)

    return {"scatter_data": list(ward_map.values())}

@router.get("/overview")
async def get_analytics_overview():
    """High-level overview stats using Firestore count aggregations."""
    db = get_nagpur_db()
    g_col = db.collection("grievance_forms")
    
    total_snap = await g_col.count().get()
    total_complaints = total_snap[0].value
    
    open_snap = await g_col.where("status", "in", ["submitted", "assigned", "in_progress", "Assigned", "In Progress", "draft"]).count().get()
    open_complaints = open_snap[0].value
    
    resolved_snap = await g_col.where("status", "in", ["resolved", "closed", "confirmed", "Resolved"]).count().get()
    resolved_complaints = resolved_snap[0].value
    
    total_wards = (await db.collection("wards").count().get())[0].value
    water_records = (await db.collection("water_supply_data").count().get())[0].value
    sanitation_records = (await db.collection("sanitation_data").count().get())[0].value

    # Most complained ward via manual stream count
    ward_counts = {}
    docs = g_col.stream()
    async for doc in docs:
        wid = doc.to_dict().get("ward_id")
        if wid:
            ward_counts[wid] = ward_counts.get(wid, 0) + 1
            
    worst_ward = None
    if ward_counts:
        worst_wid = max(ward_counts, key=ward_counts.get)
        w_doc = await db.collection("wards").document(worst_wid).get()
        if w_doc.exists:
            worst_ward = {
                "ward_id": worst_wid,
                "ward_name": w_doc.to_dict().get("ward_name"),
                "count": ward_counts[worst_wid]
            }

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
    """Aggregate dataset records manually for insights."""
    db = get_nagpur_db()
    
    # Helper for counting by field
    async def count_by_zone(coll_name):
        counts = {}
        docs = db.collection(coll_name).stream()
        async for doc in docs:
            zid = doc.to_dict().get("zone_id")
            if zid:
                counts[zid] = counts.get(zid, 0) + 1
        return [{"zone_id": z, "record_count": c} for z, c in counts.items()]

    sanitation_by_zone = await count_by_zone("sanitation_data")
    civic_by_zone = await count_by_zone("civic_metrics")
    water_by_zone = await count_by_zone("water_supply_data")

    # Ward-level heatmap counts
    ward_counts = {}
    for col in ["sanitation_data", "water_supply_data", "civic_metrics"]:
        docs = db.collection(col).stream()
        async for doc in docs:
            wid = doc.to_dict().get("ward_id")
            if wid:
                ward_counts[wid] = ward_counts.get(wid, 0) + 1
                
    max_count = max(ward_counts.values()) if ward_counts else 1
    ward_heatmap = []
    w_docs = db.collection("wards").order_by("ward_number").stream()
    async for wdoc in w_docs:
        ward = wdoc.to_dict()
        count = ward_counts.get(wdoc.id, 0)
        ward_heatmap.append({
            "ward_id": wdoc.id,
            "ward_name": ward.get("ward_name"),
            "ward_number": ward.get("ward_number"),
            "zone": ward.get("zone"),
            "zone_id": ward.get("zone_id"),
            "dataset_records": count,
            "intensity": round(count / max_count, 2),
            "population": ward.get("population", 0),
        })

    return {
        "sanitation_by_zone": sanitation_by_zone,
        "civic_by_zone": civic_by_zone,
        "water_by_zone": water_by_zone,
        "ward_dataset_heatmap": ward_heatmap,
        "total_sanitation": (await db.collection("sanitation_data").count().get())[0].value,
        "total_water": (await db.collection("water_supply_data").count().get())[0].value,
        "total_civic": (await db.collection("civic_metrics").count().get())[0].value,
    }
