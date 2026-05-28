from __future__ import annotations

import csv
import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"

DEMO_USER_ID = "a18f6ad2-2b43-4df6-9dc6-02f744f49a01"
DEMO_EMAIL = "student.khtn@what2eat.demo"
DEMO_NOW = "2026-05-18T12:00:00Z"
DEMO_LATITUDE = 10.875
DEMO_LONGITUDE = 106.8

# Same seeded hash used by the demo owners. This keeps CSV seeding deterministic.
DEMO_PASSWORD_HASH = "$2b$12$Q62h76DAHaf9ZfqfzFdst.9wftP3KZjwo04D4QAgp150DKaiv0Xxm"

DEMO_RESTAURANT_NAMES = [
    "Student Station Coffee",
    "DORMITORY COFFEE & TEA",
    "The Zero Coffee",
    "Mì Cay Naga",
    "Seoul",
    "Daegu",
    "Kimbap Sinh Viên",
    "Quán ăn vặt Hàn Quốc Tân Hòa",
    "Nhà Hàng Cơm Chay 8k",
    "Quán Cơm Thành Tài",
    "BoBaPop - Làng Đại Học",
    "IU Canteen",
    "Canteen H6",
]

FAVORITE_NAMES = [
    "Student Station Coffee",
    "DORMITORY COFFEE & TEA",
    "Mì Cay Naga",
    "Seoul",
    "Nhà Hàng Cơm Chay 8k",
]

CHECKIN_NAMES = [
    "The Zero Coffee",
    "Mì Cay Naga",
    "Quán Cơm Thành Tài",
    "BoBaPop - Làng Đại Học",
    "Canteen H6",
]

REVIEW_DATA = {
    "Student Station Coffee": (5, "Gần KTX, yên tĩnh, có ổ cắm và wifi nên rất hợp học bài trước giờ lên lớp."),
    "Mì Cay Naga": (5, "Món Hàn giá sinh viên, mì cay và tokbokki ổn, đi nhóm bạn sau giờ học rất tiện."),
    "Quán Cơm Thành Tài": (4, "Cơm trưa bình dân, gần trường, phần ăn ổn cho sinh viên."),
    "Nhà Hàng Cơm Chay 8k": (5, "Rẻ, nhẹ bụng, hợp những hôm muốn ăn chay gần Linh Trung."),
    "BoBaPop - Làng Đại Học": (4, "Trà sữa gần khu ĐHQG, giá ổn, hợp ngồi nhanh với bạn bè."),
}

SEARCH_HISTORY = [
    "quán cafe yên tĩnh có ổ cắm gần ký túc xá",
    "món hàn giá sinh viên gần làng đại học",
    "ăn trưa rẻ quanh đại học khoa học tự nhiên",
    "quán chay nhẹ bụng gần linh trung",
]


def main() -> None:
    restaurants = _load_csv("restaurants.csv")
    restaurant_by_name = _pick_demo_restaurants(restaurants)

    _upsert_rows(
        "users.csv",
        key="user_id",
        remove=lambda row: row.get("user_id") == DEMO_USER_ID or row.get("email") == DEMO_EMAIL,
        new_rows=[
            {
                "user_id": DEMO_USER_ID,
                "full_name": "Minh Anh Sinh Viên KHTN",
                "email": DEMO_EMAIL,
                "password_hash": DEMO_PASSWORD_HASH,
                "oauth_provider": "",
                "oauth_id": "",
                "role": "CUSTOMER",
                "avatar_url": "",
                "status": "ACTIVE",
                "created_at": DEMO_NOW,
            }
        ],
    )

    _upsert_rows(
        "customer_profiles.csv",
        key="customer_id",
        remove=lambda row: row.get("customer_id") == DEMO_USER_ID,
        new_rows=[
            {
                "customer_id": DEMO_USER_ID,
                "dietary_preferences": _json(["giá sinh viên", "ưu tiên gần trường/KTX", "không quá cay"]),
                "preferred_cuisines": _json(["món hàn", "cà phê / brunch", "món việt", "chay / healthy"]),
                "preferred_price_range": "15000 - 100000",
                "preferred_locations": _json(["linh trung", "làng đại học", "đhqg", "ký túc xá", "thủ đức"]),
                "loyalty_points": "120",
                "personalization_enabled": "true",
                "created_at": DEMO_NOW,
                "updated_at": DEMO_NOW,
            }
        ],
    )

    _upsert_rows(
        "favorites.csv",
        key="favorite_id",
        remove=lambda row: row.get("customer_id") == DEMO_USER_ID,
        new_rows=[
            {
                "favorite_id": _stable_uuid("favorite", name),
                "customer_id": DEMO_USER_ID,
                "restaurant_id": restaurant_by_name[name]["restaurant_id"],
                "created_at": DEMO_NOW,
            }
            for name in FAVORITE_NAMES
            if name in restaurant_by_name
        ],
    )

    _upsert_rows(
        "checkins.csv",
        key="checkin_id",
        remove=lambda row: row.get("customer_id") == DEMO_USER_ID,
        new_rows=[
            {
                "checkin_id": _stable_uuid("checkin", name),
                "customer_id": DEMO_USER_ID,
                "restaurant_id": restaurant_by_name[name]["restaurant_id"],
                "reservation_id": "",
                "menu_item_id": "",
                "checkin_at": _demo_time(index),
                "crowd_status": "VUA_PHAI",
                "note": _checkin_note(name),
                "is_verified": "true",
            }
            for index, name in enumerate(CHECKIN_NAMES)
            if name in restaurant_by_name
        ],
    )

    _upsert_rows(
        "reviews.csv",
        key="review_id",
        remove=lambda row: row.get("customer_id") == DEMO_USER_ID,
        new_rows=[
            {
                "review_id": _stable_uuid("review", name),
                "customer_id": DEMO_USER_ID,
                "restaurant_id": restaurant_by_name[name]["restaurant_id"],
                "reservation_id": "",
                "rating": str(rating),
                "comment": comment,
                "status": "APPROVED",
                "rejection_reason": "",
                "created_at": DEMO_NOW,
                "updated_at": DEMO_NOW,
            }
            for name, (rating, comment) in REVIEW_DATA.items()
            if name in restaurant_by_name
        ],
    )

    _upsert_rows(
        "search_history.csv",
        key="search_id",
        remove=lambda row: row.get("customer_id") == DEMO_USER_ID,
        new_rows=[
            {
                "search_id": _stable_uuid("search", query),
                "customer_id": DEMO_USER_ID,
                "query_text": query,
                "search_type": "AI",
                "filters_applied": _json({}),
                "extracted_entities": _json({}),
                "result_restaurant_ids": _json(_ids_for_query(query, restaurant_by_name)),
                "created_at": _demo_time(index),
            }
            for index, query in enumerate(SEARCH_HISTORY)
        ],
    )

    print(f"Seeded demo student user: {DEMO_EMAIL}")
    print(f"Linked restaurants: {len(restaurant_by_name)}")


def _pick_demo_restaurants(restaurants: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    picked: dict[str, dict[str, str]] = {}
    for name in DEMO_RESTAURANT_NAMES:
        matches = [row for row in restaurants if row.get("name") == name]
        if not matches:
            continue
        picked[name] = min(matches, key=_distance_to_demo)
    return picked


def _distance_to_demo(row: dict[str, str]) -> float:
    try:
        latitude = float(row.get("latitude") or 0)
        longitude = float(row.get("longitude") or 0)
    except ValueError:
        return math.inf
    return (latitude - DEMO_LATITUDE) ** 2 + (longitude - DEMO_LONGITUDE) ** 2


def _ids_for_query(query: str, restaurants: dict[str, dict[str, str]]) -> list[str]:
    normalized = query.lower()
    if "hàn" in normalized:
        names = ["Mì Cay Naga", "Seoul", "Daegu", "Kimbap Sinh Viên"]
    elif "cafe" in normalized or "cà phê" in normalized:
        names = ["Student Station Coffee", "DORMITORY COFFEE & TEA", "The Zero Coffee"]
    elif "chay" in normalized:
        names = ["Nhà Hàng Cơm Chay 8k"]
    else:
        names = ["Quán Cơm Thành Tài", "Canteen H6", "IU Canteen"]
    return [restaurants[name]["restaurant_id"] for name in names if name in restaurants]


def _checkin_note(name: str) -> str:
    notes = {
        "The Zero Coffee": "Ngồi học bài buổi chiều, quán có ổ cắm và khá yên tĩnh.",
        "Mì Cay Naga": "Đi ăn món Hàn với nhóm bạn sau giờ học.",
        "Quán Cơm Thành Tài": "Ăn trưa nhanh, giá sinh viên.",
        "BoBaPop - Làng Đại Học": "Mua trà sữa gần KTX.",
        "Canteen H6": "Ăn trưa quanh khu đại học.",
    }
    return notes.get(name, "Check-in demo quanh khu đại học.")


def _demo_time(index: int) -> str:
    base = datetime(2026, 5, 18 - min(index, 10), 12, 0, tzinfo=timezone.utc)
    return base.isoformat().replace("+00:00", "Z")


def _upsert_rows(
    filename: str,
    *,
    key: str,
    remove,
    new_rows: list[dict[str, str]],
) -> None:
    existing_rows = _load_csv(filename)
    fieldnames = _fieldnames(filename)
    filtered_rows = [
        {field: row.get(field, "") for field in fieldnames}
        for row in existing_rows
        if any(str(value or "").strip() for value in row.values()) and not remove(row)
    ]
    seen = {row.get(key) for row in filtered_rows}
    for row in new_rows:
        if row.get(key) in seen:
            continue
        filtered_rows.append({field: row.get(field, "") for field in fieldnames})
        seen.add(row.get(key))
    _write_csv(filename, fieldnames, filtered_rows)


def _fieldnames(filename: str) -> list[str]:
    path = DATA_DIR / filename
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        return list(reader.fieldnames or [])


def _load_csv(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def _write_csv(filename: str, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path = DATA_DIR / filename
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _stable_uuid(*parts: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "what2eat-demo-student:" + ":".join(parts)))


if __name__ == "__main__":
    main()
