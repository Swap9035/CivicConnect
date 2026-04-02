"""
Seed script to populate all 38 Nagpur wards across 10 zones.
Ward data based on Nagpur Municipal Corporation (NMC) official structure.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Nagpur's 10 administrative zones and their wards
NAGPUR_WARDS = [
    # Zone 1: Laxmi Nagar Zone
    {"_id": "ward_01", "ward_number": 1, "ward_name": "Laxmi Nagar", "zone": "Laxmi Nagar Zone", "zone_id": "zone_01",
     "area_names": ["Laxmi Nagar", "Laxminagar", "LN", "Bajaj Nagar", "Friends Colony", "Shivaji Nagar", "Seminary Hills"],
     "population": 48000, "area_sq_km": 8.2},
    {"_id": "ward_02", "ward_number": 2, "ward_name": "Dharampeth", "zone": "Laxmi Nagar Zone", "zone_id": "zone_01",
     "area_names": ["Dharampeth", "Dharam Peth", "Law College Square", "Shankar Nagar", "Ambazari"],
     "population": 52000, "area_sq_km": 7.5},
    {"_id": "ward_03", "ward_number": 3, "ward_name": "Dhantoli", "zone": "Laxmi Nagar Zone", "zone_id": "zone_01",
     "area_names": ["Dhantoli", "Civil Lines", "Reserve Bank Square", "VCA Ground"],
     "population": 38000, "area_sq_km": 5.8},
    {"_id": "ward_04", "ward_number": 4, "ward_name": "Sakkardara", "zone": "Laxmi Nagar Zone", "zone_id": "zone_01",
     "area_names": ["Sakkardara", "Sakkar Dara", "Sakkardara Square"],
     "population": 41000, "area_sq_km": 6.1},
    
    # Zone 2: Dharampeth Zone
    {"_id": "ward_05", "ward_number": 5, "ward_name": "Sitabuldi", "zone": "Dharampeth Zone", "zone_id": "zone_02",
     "area_names": ["Sitabuldi", "Sita Buldi", "Sitabuldi Fort", "Main Road Sitabuldi"],
     "population": 55000, "area_sq_km": 4.5},
    {"_id": "ward_06", "ward_number": 6, "ward_name": "Ramdaspeth", "zone": "Dharampeth Zone", "zone_id": "zone_02",
     "area_names": ["Ramdaspeth", "Ramdas Peth", "WHC Road", "South Ambazari Road"],
     "population": 44000, "area_sq_km": 6.8},
    {"_id": "ward_07", "ward_number": 7, "ward_name": "Mahal", "zone": "Dharampeth Zone", "zone_id": "zone_02",
     "area_names": ["Mahal", "Mahal Area", "Itwari", "Cotton Market"],
     "population": 60000, "area_sq_km": 5.2},
    {"_id": "ward_08", "ward_number": 8, "ward_name": "Mominpura", "zone": "Dharampeth Zone", "zone_id": "zone_02",
     "area_names": ["Mominpura", "Momin Pura", "Mominpura Square"],
     "population": 50000, "area_sq_km": 4.8},
    
    # Zone 3: Hanuman Nagar Zone
    {"_id": "ward_09", "ward_number": 9, "ward_name": "Hanuman Nagar", "zone": "Hanuman Nagar Zone", "zone_id": "zone_03",
     "area_names": ["Hanuman Nagar", "HN", "Manewada", "Besa"],
     "population": 62000, "area_sq_km": 12.5},
    {"_id": "ward_10", "ward_number": 10, "ward_name": "Narendra Nagar", "zone": "Hanuman Nagar Zone", "zone_id": "zone_03",
     "area_names": ["Narendra Nagar", "Narendra Nagar Square", "Manish Nagar"],
     "population": 48000, "area_sq_km": 9.3},
    {"_id": "ward_11", "ward_number": 11, "ward_name": "Nandanvan", "zone": "Hanuman Nagar Zone", "zone_id": "zone_03",
     "area_names": ["Nandanvan", "Nandanwan", "Nandanvan Colony", "Yashodhara Nagar"],
     "population": 55000, "area_sq_km": 8.7},
    {"_id": "ward_12", "ward_number": 12, "ward_name": "Sonegaon", "zone": "Hanuman Nagar Zone", "zone_id": "zone_03",
     "area_names": ["Sonegaon", "Sone Gaon", "Sonegaon Lake", "Subhash Nagar"],
     "population": 45000, "area_sq_km": 7.8},
    
    # Zone 4: Dhantoli Zone
    {"_id": "ward_13", "ward_number": 13, "ward_name": "Gandhibagh", "zone": "Dhantoli Zone", "zone_id": "zone_04",
     "area_names": ["Gandhibagh", "Gandhi Bagh", "Gandhibagh Market"],
     "population": 58000, "area_sq_km": 4.2},
    {"_id": "ward_14", "ward_number": 14, "ward_name": "Pachpaoli", "zone": "Dhantoli Zone", "zone_id": "zone_04",
     "area_names": ["Pachpaoli", "Pach Paoli", "Pachpaoli Square"],
     "population": 52000, "area_sq_km": 5.0},
    {"_id": "ward_15", "ward_number": 15, "ward_name": "Satranjipura", "zone": "Dhantoli Zone", "zone_id": "zone_04",
     "area_names": ["Satranjipura", "Satrangi Pura", "Satranjipura Square"],
     "population": 46000, "area_sq_km": 5.5},
    
    # Zone 5: Nehru Nagar Zone
    {"_id": "ward_16", "ward_number": 16, "ward_name": "Nehru Nagar", "zone": "Nehru Nagar Zone", "zone_id": "zone_05",
     "area_names": ["Nehru Nagar", "Nehrunagar", "Pratap Nagar", "Telephone Exchange"],
     "population": 50000, "area_sq_km": 7.1},
    {"_id": "ward_17", "ward_number": 17, "ward_name": "Jaripatka", "zone": "Nehru Nagar Zone", "zone_id": "zone_05",
     "area_names": ["Jaripatka", "Jari Patka", "Jaripatka Square"],
     "population": 42000, "area_sq_km": 6.5},
    {"_id": "ward_18", "ward_number": 18, "ward_name": "Indora", "zone": "Nehru Nagar Zone", "zone_id": "zone_05",
     "area_names": ["Indora", "Indora Square", "Kalamna"],
     "population": 45000, "area_sq_km": 8.0},
    {"_id": "ward_19", "ward_number": 19, "ward_name": "Lakadganj", "zone": "Nehru Nagar Zone", "zone_id": "zone_05",
     "area_names": ["Lakadganj", "Lakad Ganj", "Panchsheel Nagar", "Bhandara Road"],
     "population": 56000, "area_sq_km": 9.2},
    
    # Zone 6: Gandhibagh Zone
    {"_id": "ward_20", "ward_number": 20, "ward_name": "Imamwada", "zone": "Gandhibagh Zone", "zone_id": "zone_06",
     "area_names": ["Imamwada", "Imam Wada", "Punapur"],
     "population": 48000, "area_sq_km": 4.0},
    {"_id": "ward_21", "ward_number": 21, "ward_name": "Mangalwari", "zone": "Gandhibagh Zone", "zone_id": "zone_06",
     "area_names": ["Mangalwari", "Mangal Wari", "Gokulpeth"],
     "population": 43000, "area_sq_km": 5.3},
    {"_id": "ward_22", "ward_number": 22, "ward_name": "Ashi Nagar", "zone": "Gandhibagh Zone", "zone_id": "zone_06",
     "area_names": ["Ashi Nagar", "Ashinagar", "Ashi Nagar Square"],
     "population": 39000, "area_sq_km": 6.0},
    
    # Zone 7: Sataranjipura Zone
    {"_id": "ward_23", "ward_number": 23, "ward_name": "Bharatwada", "zone": "Satranjipura Zone", "zone_id": "zone_07",
     "area_names": ["Bharatwada", "Bharat Wada", "Bharatwada Khamla"],
     "population": 44000, "area_sq_km": 10.5},
    {"_id": "ward_24", "ward_number": 24, "ward_name": "Wadi", "zone": "Satranjipura Zone", "zone_id": "zone_07",
     "area_names": ["Wadi", "Wadi Nagpur", "Wadi BN"],
     "population": 40000, "area_sq_km": 8.0},
    {"_id": "ward_25", "ward_number": 25, "ward_name": "Hudkeshwar", "zone": "Satranjipura Zone", "zone_id": "zone_07",
     "area_names": ["Hudkeshwar", "Hudkeshwar Road", "Dighori"],
     "population": 47000, "area_sq_km": 11.2},
    
    # Zone 8: Lakadganj Zone
    {"_id": "ward_26", "ward_number": 26, "ward_name": "Tajbagh", "zone": "Lakadganj Zone", "zone_id": "zone_08",
     "area_names": ["Tajbagh", "Taj Bagh", "Tajbag"],
     "population": 38000, "area_sq_km": 5.5},
    {"_id": "ward_27", "ward_number": 27, "ward_name": "Sanjay Nagar", "zone": "Lakadganj Zone", "zone_id": "zone_08",
     "area_names": ["Sanjay Nagar", "Sanjaynagar"],
     "population": 42000, "area_sq_km": 6.2},
    {"_id": "ward_28", "ward_number": 28, "ward_name": "Wathoda", "zone": "Lakadganj Zone", "zone_id": "zone_08",
     "area_names": ["Wathoda", "Wathoda Layout", "Wathoda Nagpur"],
     "population": 36000, "area_sq_km": 7.8},
    
    # Zone 9: Mangalwari Zone
    {"_id": "ward_29", "ward_number": 29, "ward_name": "Hasanbagh", "zone": "Mangalwari Zone", "zone_id": "zone_09",
     "area_names": ["Hasanbagh", "Hasan Bagh", "Hasanbag"],
     "population": 41000, "area_sq_km": 4.5},
    {"_id": "ward_30", "ward_number": 30, "ward_name": "Wardhaman Nagar", "zone": "Mangalwari Zone", "zone_id": "zone_09",
     "area_names": ["Wardhaman Nagar", "Wardha Man Nagar", "Wardhamannagar"],
     "population": 45000, "area_sq_km": 7.0},
    {"_id": "ward_31", "ward_number": 31, "ward_name": "Khamla", "zone": "Mangalwari Zone", "zone_id": "zone_09",
     "area_names": ["Khamla", "Khamla Square", "Khamla Road"],
     "population": 39000, "area_sq_km": 6.3},
    {"_id": "ward_32", "ward_number": 32, "ward_name": "Pratap Nagar", "zone": "Mangalwari Zone", "zone_id": "zone_09",
     "area_names": ["Pratap Nagar", "Pratapnagar", "Pratap Nagar Square"],
     "population": 43000, "area_sq_km": 5.8},
    
    # Zone 10: Ashi Nagar Zone
    {"_id": "ward_33", "ward_number": 33, "ward_name": "Mankapur", "zone": "Ashi Nagar Zone", "zone_id": "zone_10",
     "area_names": ["Mankapur", "Man Kapur", "Mankapur Stadium"],
     "population": 50000, "area_sq_km": 9.0},
    {"_id": "ward_34", "ward_number": 34, "ward_name": "Sadar", "zone": "Ashi Nagar Zone", "zone_id": "zone_10",
     "area_names": ["Sadar", "Sadar Nagpur", "Sadar Bazaar", "Kamptee Road"],
     "population": 54000, "area_sq_km": 6.5},
    {"_id": "ward_35", "ward_number": 35, "ward_name": "Pardi", "zone": "Ashi Nagar Zone", "zone_id": "zone_10",
     "area_names": ["Pardi", "Pardi Nagpur", "Pardi Naka"],
     "population": 37000, "area_sq_km": 5.0},
    {"_id": "ward_36", "ward_number": 36, "ward_name": "Gittikhadan", "zone": "Ashi Nagar Zone", "zone_id": "zone_10",
     "area_names": ["Gittikhadan", "Gitti Khadan", "Gittikhadan Layout"],
     "population": 46000, "area_sq_km": 8.5},
    {"_id": "ward_37", "ward_number": 37, "ward_name": "Trimurtee Nagar", "zone": "Ashi Nagar Zone", "zone_id": "zone_10",
     "area_names": ["Trimurtee Nagar", "Trimurti Nagar", "Trimurtee"],
     "population": 40000, "area_sq_km": 7.2},
    {"_id": "ward_38", "ward_number": 38, "ward_name": "Gorewada", "zone": "Ashi Nagar Zone", "zone_id": "zone_10",
     "area_names": ["Gorewada", "Gorewada Zoo", "Gorewada Lake", "Gorewada Dam"],
     "population": 35000, "area_sq_km": 15.0},
]


async def seed_wards(db):
    """Seed all 38 Nagpur wards into the database if not already present."""
    existing = await db.wards.count_documents({})
    if existing >= 38:
        logger.info(f"Wards already seeded ({existing} found)")
        return
    
    # Clear and re-seed
    await db.wards.delete_many({})
    
    for ward in NAGPUR_WARDS:
        ward["created_at"] = datetime.utcnow()
        await db.wards.insert_one(ward)
    
    logger.info(f"✅ Seeded {len(NAGPUR_WARDS)} Nagpur wards across 10 zones")


async def get_ward_lookup(db) -> dict:
    """Return {ward_id: [aliases]} for ward normalization."""
    lookup = {}
    async for ward in db.wards.find({}):
        lookup[ward["_id"]] = ward.get("area_names", [ward.get("ward_name", "")])
    return lookup
