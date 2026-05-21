from __future__ import annotations

import math
import re
import sys
from pathlib import Path


RECOMMEND_SRC_CANDIDATES = (
    Path(__file__).resolve().parents[3] / "recommend_system" / "src",
    Path(__file__).resolve().parents[4] / "recommend system" / "src",
)

for recommend_src in RECOMMEND_SRC_CANDIDATES:
    if recommend_src.exists() and str(recommend_src) not in sys.path:
        sys.path.insert(0, str(recommend_src))
        break

try:
    from recommend_system.heuristics import infer_cuisines, infer_semantic_tags, parse_query_heuristically
    from recommend_system.utils import extract_district_slug_from_text, haversine_km, normalize_text, tokenize
except ImportError:  # pragma: no cover - only used when the local recommend package is missing.
    infer_cuisines = None
    infer_semantic_tags = None
    parse_query_heuristically = None

    def normalize_text(text: object) -> str:
        text = "" if text is None else str(text).lower()
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text)).strip()

    def tokenize(text: str) -> list[str]:
        return [token for token in normalize_text(text).split() if len(token) > 1]

    def extract_district_slug_from_text(text: object) -> str | None:
        normalized = normalize_text(text)
        match = re.search(r"\bquan\s*(\d{1,2})\b", normalized)
        return f"quan-{match.group(1)}" if match else None

    def haversine_km(
        latitude_a: float | None,
        longitude_a: float | None,
        latitude_b: float | None,
        longitude_b: float | None,
    ) -> float | None:
        if None in {latitude_a, longitude_a, latitude_b, longitude_b}:
            return None
        radius_km = 6371.0
        lat1 = math.radians(float(latitude_a))
        lon1 = math.radians(float(longitude_a))
        lat2 = math.radians(float(latitude_b))
        lon2 = math.radians(float(longitude_b))
        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1
        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius_km * c
