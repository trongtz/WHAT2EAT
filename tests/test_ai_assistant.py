from __future__ import annotations

import sys
import unittest
import uuid
import os
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'what2eat.db'}")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("OPENAI_API_KEY", "")

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import main  # noqa: E402,F401 - Import registers SQLAlchemy models.
import crud.ai_chat as crud_ai_chat  # noqa: E402
from core.database import SessionLocal  # noqa: E402
from schemas.ai_chat import AIChatMessageCreate, RecommendationLogCreate  # noqa: E402
from services.ai_service import generate_recommendation  # noqa: E402


class AIAssistantRecommendationTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
