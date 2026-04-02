"""
Ward name normalizer using fuzzy matching.
Maps messy area/ward names from datasets and user input to standardized ward IDs.
"""
from typing import Optional, Dict, List

try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False
    print("⚠️ rapidfuzz not installed. Falling back to exact match only.")


class WardNormalizer:
    """Maps messy area names to standardized ward IDs using fuzzy matching."""

    def __init__(self, ward_lookup: Dict[str, List[str]]):
        """
        ward_lookup: { "ward_01": ["Lakadganj", "Lakad Ganj", ...] }
        """
        self.ward_lookup = ward_lookup
        # Flatten: { "lakadganj": "ward_01", ... }
        self.flat_map = {}
        for ward_id, aliases in ward_lookup.items():
            for alias in aliases:
                self.flat_map[alias.lower().strip()] = ward_id

    def normalize(self, raw_area_name: str, threshold: int = 70) -> Optional[str]:
        """Return ward_id for a given raw area name, or None if no match."""
        if not raw_area_name or not str(raw_area_name).strip():
            return None

        clean = str(raw_area_name).lower().strip()

        # 1. Exact match
        if clean in self.flat_map:
            return self.flat_map[clean]

        # 2. Substring match — check if any alias is contained in the input
        for alias, ward_id in self.flat_map.items():
            if alias in clean or clean in alias:
                return ward_id

        # 3. Fuzzy match (if rapidfuzz available)
        if HAS_RAPIDFUZZ:
            candidates = list(self.flat_map.keys())
            result = process.extractOne(clean, candidates, scorer=fuzz.token_sort_ratio)
            if result and result[1] >= threshold:
                return self.flat_map[result[0]]

        return None

    def normalize_with_info(self, raw_area_name: str, threshold: int = 70) -> dict:
        """Return ward_id + match details."""
        ward_id = self.normalize(raw_area_name, threshold)
        if ward_id:
            ward_name = None
            for wid, aliases in self.ward_lookup.items():
                if wid == ward_id and aliases:
                    ward_name = aliases[0]
                    break
            return {"ward_id": ward_id, "ward_name": ward_name, "matched": True}
        return {"ward_id": None, "ward_name": None, "matched": False}
