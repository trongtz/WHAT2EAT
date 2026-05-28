from __future__ import annotations

import sys
import unittest
import uuid
import os
from datetime import time
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
TEST_DB_PATH = Path("/private/tmp/what2eat_ai_assistant_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("OPENAI_API_KEY", "")

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import main  # noqa: E402,F401 - Import registers SQLAlchemy models.
import crud.ai_chat as crud_ai_chat  # noqa: E402
from core.database import Base, engine  # noqa: E402
from core.database import SessionLocal  # noqa: E402
from models.capacity import Capacity  # noqa: E402
from models.restaurant import Restaurant  # noqa: E402
from models.restaurant_taxonomy import CuisineCategory, RestaurantCuisine  # noqa: E402
from models.user import User  # noqa: E402
from schemas.ai import AIRecommendationResponse, AIRestaurantMatch  # noqa: E402
from schemas.ai_chat import AIChatMessageCreate, RecommendationLogCreate  # noqa: E402
from services.ai_service import generate_recommendation  # noqa: E402


class AIAssistantRecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        _seed_test_data()

    def setUp(self) -> None:
        self.db = SessionLocal()

    def tearDown(self) -> None:
        self.db.close()

    def test_recommendation_returns_hybrid_results(self) -> None:
        response = generate_recommendation("Gợi ý cafe yên tĩnh dưới 100k", self.db, limit=3)

        self.assertEqual(response["source"], "HYBRID")
        self.assertEqual(response["filters_applied"]["cuisines"], ["cà phê / brunch"])
        self.assertGreater(len(response["recommended_restaurants"]), 0)
        self.assertTrue(all(item["id"] for item in response["recommended_restaurants"]))
        self.assertTrue(all(item["reason"] for item in response["recommended_restaurants"]))
        first_match = response["recommended_restaurants"][0]
        self.assertIn("available_capacity", first_match)
        self.assertIn("quality_score", first_match)
        self.assertIn("availability_score", first_match)
        self.assertIn("quality_signals", first_match)

    def test_api_response_schema_keeps_recommendation_signals(self) -> None:
        response = AIRecommendationResponse(
            message="ok",
            total_found=1,
            recommended_restaurants=[
                AIRestaurantMatch(
                    id=str(uuid.uuid4()),
                    name="Test Cafe",
                    address="Quận 1",
                    distance_km=0.4,
                    match_score=0.9,
                    reason="Gần bạn.",
                    available_capacity=12,
                    quality_score=0.82,
                    availability_score=0.75,
                    quality_signals={"rating_avg": 4.5, "checkin_count_30d": 30},
                )
            ],
            source="HYBRID",
        )

        payload = response.model_dump()
        match = payload["recommended_restaurants"][0]
        self.assertEqual(match["available_capacity"], 12)
        self.assertEqual(match["quality_score"], 0.82)
        self.assertEqual(match["availability_score"], 0.75)
        self.assertEqual(match["quality_signals"]["checkin_count_30d"], 30)

    def test_recommendation_applies_default_radius_when_location_is_present(self) -> None:
        response = generate_recommendation(
            "quán cafe yên tĩnh gần đây dưới 100k",
            self.db,
            latitude=10.7738,
            longitude=106.704,
            limit=5,
        )

        self.assertEqual(response["filters_applied"]["radius_km"], 2.0)
        self.assertGreater(len(response["recommended_restaurants"]), 0)
        self.assertTrue(
            all(
                item["distance_km"] is not None and item["distance_km"] <= 2.0
                for item in response["recommended_restaurants"]
            )
        )

    def test_follow_up_uses_context_and_avoids_repeated_results(self) -> None:
        session_id = uuid.uuid4()
        first_query = "Tìm quán lẩu cho 4 người, giá khoảng 100k đến 200k"
        session = crud_ai_chat.get_or_create_session(self.db, session_id, None, title="test follow up")
        self.assertEqual(session.session_id, session_id)

        crud_ai_chat.create_message(
            self.db,
            session_id,
            AIChatMessageCreate(role="user", content=first_query),
        )
        first_response = generate_recommendation(first_query, self.db, session_id=session_id, limit=3)
        for index, restaurant in enumerate(first_response["recommended_restaurants"], start=1):
            crud_ai_chat.create_recommendation_log(
                self.db,
                RecommendationLogCreate(
                    session_id=session_id,
                    restaurant_id=uuid.UUID(restaurant["id"]),
                    score=restaurant["match_score"],
                    reason=restaurant["reason"],
                    source="HYBRID",
                    rank_position=index,
                    prompt_summary=first_query,
                ),
            )

        follow_up = generate_recommendation("quán khác rẻ hơn", self.db, session_id=session_id, limit=3)

        self.assertTrue(follow_up["context_used"]["use_previous_context"])
        self.assertTrue(follow_up["context_used"]["avoid_repeated_results"])
        self.assertEqual(follow_up["filters_applied"]["cuisines"], ["lẩu"])
        self.assertEqual(follow_up["filters_applied"]["group_size"], 4)
        first_ids = {item["id"] for item in first_response["recommended_restaurants"]}
        follow_up_ids = {item["id"] for item in follow_up["recommended_restaurants"]}
        self.assertFalse(first_ids & follow_up_ids)


def _seed_test_data() -> None:
    owner_id = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
    cafe_category_id = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000101")
    hotpot_category_id = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000102")
    restaurants = [
        (
            uuid.UUID("cccccccc-0000-0000-0000-000000001001"),
            "Cà Phê Test Yên Tĩnh",
            "Quán cà phê yên tĩnh, có trà sữa và không gian làm việc.",
            "Quận 1, TP. HCM",
            10.7738,
            106.7040,
            "50000 - 100000",
            cafe_category_id,
        ),
        (
            uuid.UUID("cccccccc-0000-0000-0000-000000001002"),
            "Lẩu Test Một",
            "Nhà hàng lẩu hotpot phù hợp nhóm 4 người.",
            "Quận 1, TP. HCM",
            10.7740,
            106.7042,
            "100000 - 200000",
            hotpot_category_id,
        ),
        (
            uuid.UUID("cccccccc-0000-0000-0000-000000001003"),
            "Lẩu Test Hai",
            "Quán lẩu hotpot bình dân.",
            "Quận 3, TP. HCM",
            10.7790,
            106.6900,
            "100000 - 200000",
            hotpot_category_id,
        ),
        (
            uuid.UUID("cccccccc-0000-0000-0000-000000001004"),
            "Lẩu Test Ba",
            "Lẩu cay, phù hợp nhóm bạn.",
            "Quận 5, TP. HCM",
            10.7550,
            106.6700,
            "100000 - 200000",
            hotpot_category_id,
        ),
        (
            uuid.UUID("cccccccc-0000-0000-0000-000000001005"),
            "Lẩu Test Bốn",
            "Hotpot giá ổn, còn nhiều chỗ.",
            "Quận 10, TP. HCM",
            10.7700,
            106.6600,
            "100000 - 200000",
            hotpot_category_id,
        ),
    ]

    db = SessionLocal()
    try:
        db.add(
            User(
                user_id=owner_id,
                full_name="Test Owner",
                email="owner-ai-test@what2eat.local",
                password_hash="test",
                role="OWNER",
                status="ACTIVE",
            )
        )
        db.commit()
        db.add_all(
            [
                CuisineCategory(category_id=cafe_category_id, name="Cà phê (Coffee)"),
                CuisineCategory(category_id=hotpot_category_id, name="Lẩu (Hotpot)"),
            ]
        )
        db.commit()
        for restaurant_id, name, description, address, latitude, longitude, price_range, category_id in restaurants:
            db.add(
                Restaurant(
                    restaurant_id=restaurant_id,
                    owner_id=owner_id,
                    name=name,
                    description=description,
                    address=address,
                    latitude=latitude,
                    longitude=longitude,
                    price_range=price_range,
                    rating_avg=4.5,
                    approval_status="APPROVED",
                    is_active=True,
                )
            )
            db.commit()
            db.add(RestaurantCuisine(restaurant_id=restaurant_id, category_id=category_id))
            db.commit()
            db.add(
                Capacity(
                    capacity_id=uuid.uuid4(),
                    restaurant_id=restaurant_id,
                    day_of_week=0,
                    start_time=time(8, 0),
                    end_time=time(22, 0),
                    max_capacity=40,
                )
            )
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    unittest.main()
