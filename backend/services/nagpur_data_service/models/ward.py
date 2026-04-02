from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Ward(BaseModel):
    ward_id: str = Field(..., alias="_id")
    ward_number: int
    ward_name: str
    zone: str
    zone_id: str
    area_names: List[str] = []  # All known aliases for fuzzy matching
    population: Optional[int] = None
    area_sq_km: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class WardStats(BaseModel):
    ward_id: str
    ward_name: str
    zone: str
    total_complaints: int = 0
    open_complaints: int = 0
    resolved_complaints: int = 0
    avg_resolution_hours: Optional[float] = None
    top_category: Optional[str] = None
    water_supply_score: Optional[float] = None
    sanitation_score: Optional[float] = None
    health_score: Optional[float] = None  # Composite 0-100


class WaterSupplyRecord(BaseModel):
    ward_id: str
    zone_id: str
    area_name: Optional[str] = None
    issue_type: Optional[str] = None
    supply_hours_per_day: Optional[float] = None
    scheduled_supply_hours: Optional[float] = None
    source: Optional[str] = None
    pipeline_age_years: Optional[int] = None
    affected_households: Optional[int] = None
    reported_date: Optional[str] = None
    data_source: Optional[str] = None
    imported_at: datetime = Field(default_factory=datetime.utcnow)


class SanitationRecord(BaseModel):
    ward_id: str
    zone_id: str
    area_name: Optional[str] = None
    metric_type: Optional[str] = None
    daily_waste_tons: Optional[float] = None
    collection_frequency: Optional[str] = None
    missed_collections_last_month: Optional[int] = None
    drain_blockage_count: Optional[int] = None
    public_toilets_count: Optional[int] = None
    swachh_bharat_score: Optional[float] = None
    reported_month: Optional[str] = None
    data_source: Optional[str] = None
    imported_at: datetime = Field(default_factory=datetime.utcnow)


class CivicMetric(BaseModel):
    ward_id: str
    zone_id: str
    metric_category: Optional[str] = None  # roads, streetlights, parks, drainage
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    measurement_date: Optional[str] = None
    data_source: Optional[str] = None
    imported_at: datetime = Field(default_factory=datetime.utcnow)


class HeatmapDataPoint(BaseModel):
    ward_id: str
    ward_name: str
    zone: str
    count: int
    intensity: float  # 0.0 to 1.0 normalized


class TrendDataPoint(BaseModel):
    date: str
    count: int
    category: Optional[str] = None


class WardRanking(BaseModel):
    rank: int
    ward_id: str
    ward_name: str
    zone: str
    complaint_count: int
    avg_resolution_hours: Optional[float] = None
    score: Optional[float] = None
