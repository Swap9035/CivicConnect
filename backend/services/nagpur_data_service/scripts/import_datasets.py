"""
Universal CSV dataset importer for Nagpur civic data.
Auto-detects column types and maps to appropriate collections.
Normalizes area/ward names using fuzzy matching.

Usage:
    python -m services.nagpur_data_service.scripts.import_datasets
"""
import asyncio
import os
import sys
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Column name patterns for auto-detection
WATER_KEYWORDS = ["water", "supply", "pipeline", "leakage", "pressure", "tanker", "tap", "sanitation"]
SANITATION_KEYWORDS = ["waste", "garbage", "drain", "toilet", "swachh", "sewage", "cleaning", "solid waste", "slum"]
CIVIC_KEYWORDS = ["road", "pothole", "streetlight", "park", "bridge", "footpath", "electric", "lighting", "luminaire", "consumption"]


def detect_dataset_type(columns: list) -> str:
    """Auto-detect dataset type from column names."""
    cols_lower = " ".join([c.lower() for c in columns])
    
    water_score = sum(1 for kw in WATER_KEYWORDS if kw in cols_lower)
    sanitation_score = sum(1 for kw in SANITATION_KEYWORDS if kw in cols_lower)
    civic_score = sum(1 for kw in CIVIC_KEYWORDS if kw in cols_lower)

    if water_score >= sanitation_score and water_score >= civic_score and water_score > 0:
        return "water_supply"
    elif sanitation_score >= water_score and sanitation_score >= civic_score and sanitation_score > 0:
        return "sanitation"
    elif civic_score > 0:
        return "civic_metrics"
    
    return "civic_metrics"  # Default fallback


def find_area_column(columns: list) -> str:
    """Find the column most likely to contain area/ward names.
    Prioritizes 'Zone Name' since ward-level matching works via zone names too."""
    # Priority order: ward name > zone name > other area keywords
    priority_keywords = ["ward name", "ward_name", "zone name", "zone_name", "area", "ward", "locality", "location", "place", "zone", "region", "prabhag", "division", "constitutency"]
    cols_lower = {c: c.lower().strip() for c in columns}
    
    for kw in priority_keywords:
        for col, lower in cols_lower.items():
            if kw == lower or kw in lower:
                return col
    
    return None


async def import_csv_file(filepath: str, db, normalizer):
    """Import a single CSV file into the appropriate collection."""
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas is required. Install with: pip install pandas")
        return 0
    
    filename = os.path.basename(filepath)
    logger.info(f"📄 Processing: {filename}")
    
    try:
        # Try multiple encodings
        for encoding in ['utf-8', 'latin1', 'cp1252']:
            try:
                df = pd.read_csv(filepath, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            logger.error(f"  ❌ Cannot decode {filename}")
            return 0
        
        if df.empty:
            logger.warning(f"  ⚠️ Empty file: {filename}")
            return 0
        
        # Standardize column names
        df.columns = df.columns.str.strip()
        original_cols = list(df.columns)
        
        # Detect dataset type
        dataset_type = detect_dataset_type(original_cols)
        collection_name = f"{dataset_type}_data" if dataset_type != "civic_metrics" else "civic_metrics"
        logger.info(f"  📊 Detected type: {dataset_type} → collection: {collection_name}")
        logger.info(f"  📋 Columns: {original_cols}")
        
        # Find and normalize area/ward column
        area_col = find_area_column(original_cols)
        if area_col and normalizer:
            logger.info(f"  🗺️ Ward column: {area_col}")
            df["ward_id"] = df[area_col].apply(lambda x: normalizer.normalize(str(x)) if pd.notna(x) else None)
            
            # Get zone_id from ward_id
            ward_zone_map = {}
            async for ward in db.wards.find({}, {"_id": 1, "zone_id": 1}):
                ward_zone_map[ward["_id"]] = ward["zone_id"]
            
            df["zone_id"] = df["ward_id"].apply(lambda x: ward_zone_map.get(x))
            
            matched = df["ward_id"].notna().sum()
            total = len(df)
            logger.info(f"  ✅ Ward matching: {matched}/{total} rows matched ({round(matched/max(total,1)*100)}%)")
            
            unmatched = df[df["ward_id"].isna()][area_col].dropna().unique()[:5]
            if len(unmatched) > 0:
                logger.info(f"  ⚠️ Sample unmatched: {list(unmatched)}")
        else:
            df["ward_id"] = None
            df["zone_id"] = None
        
        # Add metadata
        df["data_source"] = filename
        df["imported_at"] = datetime.utcnow()
        
        # Convert to records and insert
        # Handle NaN values
        records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    record[col] = None
                elif hasattr(val, 'item'):  # numpy type
                    record[col] = val.item()
                else:
                    record[col] = val
            records.append(record)
        
        if records:
            collection = db[collection_name]
            await collection.insert_many(records)
            logger.info(f"  ✅ Imported {len(records)} records into {collection_name}")
        
        return len(records)
        
    except Exception as e:
        logger.error(f"  ❌ Error importing {filename}: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def import_all_datasets(data_dir: str = None):
    """Import all CSV files from backend/data/ directory."""
    from services.nagpur_data_service.db.connection import connect_nagpur_db, get_nagpur_db
    from services.nagpur_data_service.scripts.seed_wards import seed_wards, get_ward_lookup
    from services.nagpur_data_service.utils.ward_normalizer import WardNormalizer
    
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
    
    data_dir = os.path.abspath(data_dir)
    
    if not os.path.exists(data_dir):
        logger.error(f"❌ Data directory not found: {data_dir}")
        logger.info("Please create backend/data/ and place your CSV files there.")
        return
    
    # Connect to DB
    db = await connect_nagpur_db()
    
    # Seed wards first
    await seed_wards(db)
    
    # Build ward normalizer
    ward_lookup = await get_ward_lookup(db)
    normalizer = WardNormalizer(ward_lookup)
    
    # Find all CSV files
    csv_files = [f for f in os.listdir(data_dir) if f.lower().endswith('.csv')]
    
    if not csv_files:
        logger.info(f"📁 No CSV files found in {data_dir}")
        logger.info("Place your dataset CSV files in the backend/data/ directory.")
        return
    
    logger.info(f"📁 Found {len(csv_files)} CSV files in {data_dir}")
    
    total_imported = 0
    for csv_file in csv_files:
        filepath = os.path.join(data_dir, csv_file)
        count = await import_csv_file(filepath, db, normalizer)
        total_imported += count
    
    logger.info(f"\n🎉 Import complete! Total records imported: {total_imported}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    # Add project root to path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    sys.path.insert(0, project_root)
    
    asyncio.run(import_all_datasets())
