from __future__ import annotations

import sys
import unittest
import uuid
import os
from datetime import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


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
from core.config import settings  # noqa: E402
from models.capacity import Capacity  # noqa: E402
from models.dish import MenuItem  # noqa: E402
from models.restaurant import Restaurant  # noqa: E402
from models.restaurant_taxonomy import CuisineCategory, RestaurantCuisine  # noqa: E402
from models.user import User  # noqa: E402
from schemas.ai import AIRecommendationResponse, AIRestaurantMatch  # noqa: E402
from schemas.ai_chat import AIChatMessageCreate, AIChatSessionUpdate, RecommendationLogCreate  # noqa: E402
from services.ai_service import generate_recommendation  # noqa: E402
from services.ai_assistant.agent import serialize_agent_state  # noqa: E402
from services.ai_assistant.tools import passes_hard_constraints  # noqa: E402
from services.ai_assistant.intent_extractor import extract_intent  # noqa: E402
from services.ai_assistant.openai_intent_parser import parse_intent_with_openai  # noqa: E402
from services.ai_assistant.recommend_imports import parse_query_heuristically  # noqa: E402
from services.ai_assistant.openai_response_client import OpenAIResponsesError  # noqa: E402
from services.ai_assistant.response_composer import build_message  # noqa: E402


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

    def test_korean_cuisine_does_not_match_generic_nha_hang(self) -> None:
        generic_restaurant = SimpleNamespace(
            name="Nhà hàng Mimosa",
            description="Nhà hàng món Việt gần trường, phù hợp ăn trưa.",
            address="Thủ Đức, TP. HCM",
            price_range="50000 - 100000",
            cuisine_type="Nhà hàng",
        )
        korean_restaurant = SimpleNamespace(
            name="Seoul",
            description="Quán món Hàn Quốc có tokbokki, kimbap và mì cay.",
            address="Thủ Đức, TP. HCM",
            price_range="50000 - 100000",
            cuisine_type="Món Hàn",
        )
        intent = {"cuisines": ["món hàn"]}

        self.assertFalse(passes_hard_constraints(generic_restaurant, intent))
        self.assertTrue(passes_hard_constraints(korean_restaurant, intent))

    def test_korean_cuisine_does_not_match_japanese_restaurant_with_kimchi_side(self) -> None:
        japanese_restaurant = SimpleNamespace(
            name="Uchi Sushi",
            description="Quán món ăn Nhật Bản có sashimi và sushi.",
            address="Thủ Đức, TP. HCM",
            price_range="50000 - 100000",
            cuisine_type="Món Nhật",
            cuisine_links=[],
            menu_items=[
                SimpleNamespace(
                    name="Kim chi",
                    description="Món ăn kèm.",
                    category="Đồ ăn",
                    availability_status="AVAILABLE",
                )
            ],
        )

        self.assertFalse(passes_hard_constraints(japanese_restaurant, {"cuisines": ["món hàn"]}))

    def test_parser_handles_slang_group_preferences_and_conflicts(self) -> None:
        slang_intent = parse_query_heuristically("đồ ăn hssv, bún bò huếeee")
        self.assertEqual(slang_intent.budget_label, "binh_dan")
        self.assertIn("món việt", slang_intent.cuisines)
        self.assertIn("bún bò Huế", slang_intent.dish_terms)

        soupy_intent = parse_query_heuristically("Tôi muốn ăn đồ nước nhưng không phải mì cay")
        self.assertIn("soupy_food", soupy_intent.preference_tags)
        self.assertIn("mi cay", soupy_intent.excluded_keywords)

        group_intent = parse_query_heuristically("Nhóm tôi có 4 người, có trẻ em và muốn ngồi ngoài trời")
        self.assertEqual(group_intent.group_size, 4)
        self.assertIn("kid_friendly", group_intent.preference_tags)
        self.assertIn("outdoor_seating", group_intent.preference_tags)

        conflict_intent = parse_query_heuristically("Tôi muốn ăn buffet dưới 30k")
        self.assertTrue(conflict_intent.conflicts)

    def test_negative_spicy_preference_is_remembered_across_turns(self) -> None:
        session_id = uuid.uuid4()
        crud_ai_chat.get_or_create_session(self.db, session_id, None, title="avoid spicy")
        crud_ai_chat.create_message(
            self.db,
            session_id,
            AIChatMessageCreate(role="user", content="Tôi ghét ăn cay"),
        )

        response = generate_recommendation("Gợi ý món dễ ăn đi", self.db, session_id=session_id, limit=10)

        self.assertIn("cay", response["filters_applied"]["excluded_keywords"])
        names = {restaurant["name"] for restaurant in response["recommended_restaurants"]}
        self.assertNotIn("Lẩu Test Ba", names)

    def test_walking_query_caps_radius_and_distance_lookup_returns_direct_answer(self) -> None:
        walking_response = generate_recommendation(
            "tôi muốn ăn cơm, nhưng chỉ muốn trong tầm phạm vi đi bộ 5km thôi",
            self.db,
            latitude=10.7738,
            longitude=106.704,
            limit=5,
        )
        self.assertEqual(walking_response["filters_applied"]["radius_km"], 1.5)
        self.assertTrue(walking_response["filters_applied"]["conflicts"])

        distance_response = generate_recommendation(
            "Từ vị trí hiện tại tới Cà Phê Test Yên Tĩnh bao xa",
            self.db,
            latitude=10.7738,
            longitude=106.704,
            limit=5,
        )
        self.assertEqual(distance_response["total_found"], 1)
        self.assertEqual(distance_response["recommended_restaurants"][0]["name"], "Cà Phê Test Yên Tĩnh")
        self.assertIn("khoảng 0.0 km", distance_response["message"])

    def test_negative_cuisine_overrides_previous_positive_context(self) -> None:
        session_id = uuid.uuid4()
        crud_ai_chat.get_or_create_session(self.db, session_id, None, title="avoid korean")
        crud_ai_chat.create_message(
            self.db,
            session_id,
            AIChatMessageCreate(role="user", content="Tôi muốn ăn món Hàn"),
        )

        response = generate_recommendation("Đừng gợi ý đồ Hàn nữa", self.db, session_id=session_id, limit=5)

        self.assertIn("món hàn", response["filters_applied"]["excluded_cuisines"])
        self.assertNotIn("món hàn", response["filters_applied"]["cuisines"])

    def test_empty_light_meal_response_explains_constraints(self) -> None:
        message = build_message(
            "Gợi ý món ăn nhẹ thôi",
            [],
            {"preference_tags": ["light_meal"], "excluded_keywords": ["com"]},
        )

        self.assertIn("món ăn nhẹ", message)
        self.assertIn("tránh cơm", message)
        self.assertIn("không bù", message)

    def test_slang_dish_query_matches_available_menu_item(self) -> None:
        response = generate_recommendation("Có quán nào bán mì trộn hong", self.db, limit=5)

        self.assertGreater(len(response["recommended_restaurants"]), 0)
        self.assertEqual(response["recommended_restaurants"][0]["name"], "Lẩu Test Hai")

    def test_parser_handles_vague_time_weather_and_walking_queries(self) -> None:
        vague_intent = parse_query_heuristically("Nay không biết ăn gì luôn")
        self.assertIn("easy_to_eat", vague_intent.preference_tags)

        late_night_intent = parse_query_heuristically("Đêm khuya có gì ăn được?")
        self.assertTrue(late_night_intent.open_now)
        self.assertIn("an_dem", late_night_intent.occasion_tags)

        cooling_intent = parse_query_heuristically("Trời nóng, gợi ý món làm mát cơ thể")
        self.assertIn("troi_nong", cooling_intent.weather_tags)
        self.assertIn("cooling_food", cooling_intent.preference_tags)

        walking_intent = parse_query_heuristically("Tôi muốn đi bộ nhưng quán cách 5km")
        self.assertTrue(walking_intent.walking_only)
        self.assertTrue(walking_intent.conflicts)

    def test_soupy_food_constraint_excludes_drinks_and_spicy_food(self) -> None:
        intent = {"preference_tags": ["soupy_food"], "excluded_keywords": ["cay", "mi cay"]}
        coffee = SimpleNamespace(
            name="Coffee Test",
            description="Quán cà phê có nhiều nước uống.",
            cuisine_type="Cà phê",
            address="Thủ Đức",
            price_range="20000 - 50000",
        )
        pho = SimpleNamespace(
            name="Phở Test",
            description="Quán phở bò nước dùng thanh.",
            cuisine_type="Món Việt",
            address="Thủ Đức",
            price_range="30000 - 50000",
        )
        spicy_noodles = SimpleNamespace(
            name="Mì Cay Test",
            description="Quán mì cay nước dùng đậm vị.",
            cuisine_type="Món Hàn",
            address="Thủ Đức",
            price_range="30000 - 50000",
        )

        self.assertFalse(passes_hard_constraints(coffee, intent))
        self.assertTrue(passes_hard_constraints(pho, intent))
        self.assertFalse(passes_hard_constraints(spicy_noodles, intent))

    def test_agentic_reranker_reorders_valid_ids_and_ignores_invented_ids(self) -> None:
        mocked_agentic_response = {
            "assistant_message": "Mình ưu tiên lựa chọn hợp bối cảnh của bạn và vẫn còn chỗ.",
            "ranked_results": [
                {"id": "invented-restaurant-id", "reason": "Không được dùng."},
                {
                    "id": "cccccccc-0000-0000-0000-000000001004",
                    "reason": "Không gian phù hợp và hiện còn đủ chỗ.",
                },
                {
                    "id": "cccccccc-0000-0000-0000-000000001002",
                    "reason": "Phù hợp đi nhóm và mức giá dễ cân đối.",
                },
            ],
        }
        with (
            patch.object(settings, "OPENAI_API_KEY", "test-key"),
            patch.object(settings, "OPENAI_INTENT_PARSER", False),
            patch.object(settings, "OPENAI_AGENTIC_RERANKER", True),
            patch("services.ai_assistant.openai_reranker.request_structured_json", return_value=mocked_agentic_response),
        ):
            response = generate_recommendation("Gợi ý món dễ ăn đi", self.db, limit=2)

        self.assertEqual(response["source"], "HYBRID_AGENTIC")
        self.assertTrue(response["agentic"]["used"])
        self.assertEqual(response["message"], mocked_agentic_response["assistant_message"])
        self.assertEqual(
            [item["id"] for item in response["recommended_restaurants"]],
            [
                "cccccccc-0000-0000-0000-000000001004",
                "cccccccc-0000-0000-0000-000000001002",
            ],
        )
        self.assertNotIn("invented-restaurant-id", response["result_restaurant_ids"])

    def test_agentic_reranker_falls_back_to_offline_ranking_on_api_error(self) -> None:
        with (
            patch.object(settings, "OPENAI_API_KEY", "test-key"),
            patch.object(settings, "OPENAI_INTENT_PARSER", False),
            patch.object(settings, "OPENAI_AGENTIC_RERANKER", True),
            patch(
                "services.ai_assistant.openai_reranker.request_structured_json",
                side_effect=OpenAIResponsesError("timeout"),
            ),
        ):
            response = generate_recommendation("Gợi ý món dễ ăn đi", self.db, limit=2)

        self.assertEqual(response["source"], "HYBRID")
        self.assertFalse(response["agentic"]["used"])
        self.assertEqual(response["agentic"]["fallback"], "offline_ranking")
        self.assertEqual(len(response["recommended_restaurants"]), 2)

    def test_openai_intent_parser_normalizes_structured_output(self) -> None:
        mocked_intent_response = {
            "keywords": ["healthy", "gần", "trường"],
            "cuisines": [],
            "districts": [],
            "ambience_tags": [],
            "amenity_tags": [],
            "occasion_tags": [],
            "weather_tags": [],
            "price_min": None,
            "price_max": 100000,
            "budget_label": "binh_dan",
            "group_size": None,
            "open_now": None,
            "excluded_cuisines": [],
            "excluded_keywords": [],
            "preference_tags": ["healthy"],
            "dish_terms": [],
            "conflicts": [],
            "walking_only": False,
            "notes": [],
        }
        with (
            patch.object(settings, "OPENAI_API_KEY", "test-key"),
            patch(
                "services.ai_assistant.openai_intent_parser.request_structured_json",
                return_value=mocked_intent_response,
            ) as mocked_request,
        ):
            intent = parse_intent_with_openai("Tìm món healthy gần trường dưới 100k")

        self.assertEqual(intent["parser_mode"], "openai")
        self.assertEqual(intent["price_max"], 100000)
        self.assertEqual(intent["preference_tags"], ["healthy"])
        self.assertEqual(mocked_request.call_args.kwargs["schema_name"], "restaurant_intent")

    def test_openai_intent_is_sanitized_by_local_heuristics(self) -> None:
        openai_intent = {
            "original_query": "Nhóm tôi có 4 người trong phạm vi dưới 500m",
            "normalized_query": "nhom toi co 4 nguoi trong pham vi duoi 500m",
            "keywords": ["nhóm", "500m"],
            "cuisines": ["món việt"],
            "districts": [],
            "ambience_tags": [],
            "amenity_tags": [],
            "occasion_tags": [],
            "weather_tags": [],
            "price_min": None,
            "price_max": 500,
            "budget_label": None,
            "group_size": 4,
            "open_now": None,
            "excluded_cuisines": [],
            "excluded_keywords": [],
            "preference_tags": [],
            "dish_terms": [],
            "conflicts": [],
            "walking_only": False,
            "parser_mode": "openai",
            "notes": [],
        }

        with (
            patch("services.ai_assistant.intent_extractor.should_use_openai_intent_parser", return_value=True),
            patch("services.ai_assistant.intent_extractor.parse_intent_with_openai", return_value=openai_intent),
        ):
            intent = extract_intent("Nhóm tôi có 4 người trong phạm vi dưới 500m")

        self.assertIsNone(intent["price_max"])
        self.assertEqual(intent["group_size"], 4)

    def test_openai_price_keeps_local_k_suffix_normalization(self) -> None:
        openai_intent = {
            "original_query": "Tôi muốn ăn món Hàn dưới 150k gần KTX",
            "normalized_query": "toi muon an mon han duoi 150k gan ktx",
            "keywords": ["món hàn", "150k"],
            "cuisines": ["món hàn"],
            "districts": [],
            "ambience_tags": [],
            "amenity_tags": [],
            "occasion_tags": [],
            "weather_tags": [],
            "price_min": None,
            "price_max": 150,
            "budget_label": "binh_dan",
            "group_size": None,
            "open_now": None,
            "excluded_cuisines": [],
            "excluded_keywords": [],
            "preference_tags": [],
            "dish_terms": [],
            "conflicts": [],
            "walking_only": False,
            "parser_mode": "openai",
            "notes": [],
        }

        with (
            patch("services.ai_assistant.intent_extractor.should_use_openai_intent_parser", return_value=True),
            patch("services.ai_assistant.intent_extractor.parse_intent_with_openai", return_value=openai_intent),
        ):
            intent = extract_intent("Tôi muốn ăn món Hàn dưới 150k gần KTX")

        self.assertEqual(intent["price_max"], 150000)

    def test_broad_prompt_does_not_keep_openai_guessed_hard_food_filters(self) -> None:
        openai_intent = {
            "original_query": "Nay không biết ăn gì luôn",
            "normalized_query": "nay khong biet an gi luon",
            "keywords": ["ăn tối"],
            "cuisines": ["món việt"],
            "districts": [],
            "ambience_tags": [],
            "amenity_tags": [],
            "occasion_tags": [],
            "weather_tags": [],
            "price_min": None,
            "price_max": None,
            "budget_label": None,
            "group_size": None,
            "open_now": None,
            "excluded_cuisines": [],
            "excluded_keywords": [],
            "preference_tags": ["easy_to_eat"],
            "dish_terms": ["cơm"],
            "conflicts": [],
            "walking_only": False,
            "parser_mode": "openai",
            "notes": [],
        }

        with (
            patch("services.ai_assistant.intent_extractor.should_use_openai_intent_parser", return_value=True),
            patch("services.ai_assistant.intent_extractor.parse_intent_with_openai", return_value=openai_intent),
        ):
            intent = extract_intent("Nay không biết ăn gì luôn")

        self.assertEqual(intent["cuisines"], [])
        self.assertEqual(intent["dish_terms"], [])
        self.assertIn("easy_to_eat", intent["preference_tags"])

    def test_contextual_weather_prompt_does_not_keep_openai_guessed_cuisine(self) -> None:
        openai_intent = {
            "original_query": "Trời nóng, gợi ý món làm mát cơ thể",
            "normalized_query": "troi nong goi y mon lam mat co the",
            "keywords": ["trời nóng", "làm mát"],
            "cuisines": ["món việt"],
            "districts": [],
            "ambience_tags": [],
            "amenity_tags": [],
            "occasion_tags": [],
            "weather_tags": ["troi_nong"],
            "price_min": None,
            "price_max": None,
            "budget_label": None,
            "group_size": None,
            "open_now": None,
            "excluded_cuisines": [],
            "excluded_keywords": [],
            "preference_tags": ["cooling_food"],
            "dish_terms": [],
            "conflicts": [],
            "walking_only": False,
            "parser_mode": "openai",
            "notes": [],
        }

        with (
            patch("services.ai_assistant.intent_extractor.should_use_openai_intent_parser", return_value=True),
            patch("services.ai_assistant.intent_extractor.parse_intent_with_openai", return_value=openai_intent),
        ):
            intent = extract_intent("Trời nóng, gợi ý món làm mát cơ thể")

        self.assertEqual(intent["cuisines"], [])
        self.assertIn("cooling_food", intent["preference_tags"])

    def test_agent_selects_restaurant_by_previous_result_rank(self) -> None:
        session_id = uuid.uuid4()
        crud_ai_chat.get_or_create_session(self.db, session_id, None, title="agent select")
        first_response = generate_recommendation("Tìm quán lẩu cho 4 người", self.db, session_id=session_id, limit=3)
        self._log_recommendations(session_id, "Tìm quán lẩu cho 4 người", first_response)
        expected_restaurant = first_response["recommended_restaurants"][1]

        response = generate_recommendation("quán thứ 2 được đó", self.db, session_id=session_id)

        self.assertEqual(response["source"], "AGENT")
        self.assertEqual(response["agent"]["status"], "restaurant_selected")
        self.assertEqual(response["recommended_restaurants"][0]["id"], expected_restaurant["id"])
        self.assertIn(expected_restaurant["name"], response["message"])

    def test_openai_agent_planner_action_selects_restaurant(self) -> None:
        session_id = uuid.uuid4()
        crud_ai_chat.get_or_create_session(self.db, session_id, None, title="agent openai select")
        first_response = generate_recommendation("Tìm quán lẩu cho 4 người", self.db, session_id=session_id, limit=3)
        self._log_recommendations(session_id, "Tìm quán lẩu cho 4 người", first_response)
        expected_restaurant = first_response["recommended_restaurants"][1]
        planned_action = {
            "action": "select_restaurant",
            "restaurant_ref": "quán thứ 2",
            "restaurant_rank": 2,
            "restaurant_id": None,
            "guest_count": None,
            "reservation_time_text": None,
            "confirmation": False,
            "missing_fields": [],
            "preference_note": None,
            "user_visible_message": None,
            "planner_mode": "openai",
        }

        with (
            patch.object(settings, "OPENAI_API_KEY", "test-key"),
            patch.object(settings, "OPENAI_AGENT_PLANNER", True),
            patch("services.ai_assistant.agent.plan_agent_action", return_value=planned_action),
        ):
            response = generate_recommendation("quán này ổn á", self.db, session_id=session_id)

        self.assertEqual(response["source"], "AGENT")
        self.assertEqual(response["agent"]["planner_mode"], "openai")
        self.assertEqual(response["agent"]["action"], "select_restaurant")
        self.assertEqual(response["recommended_restaurants"][0]["id"], expected_restaurant["id"])

    def test_agent_asks_for_missing_booking_info(self) -> None:
        session_id = uuid.uuid4()
        crud_ai_chat.get_or_create_session(self.db, session_id, None, title="agent missing info")
        first_response = generate_recommendation("Tìm quán lẩu cho 4 người", self.db, session_id=session_id, limit=3)
        self._log_recommendations(session_id, "Tìm quán lẩu cho 4 người", first_response)

        response = generate_recommendation("đặt quán thứ 1", self.db, session_id=session_id)

        self.assertEqual(response["source"], "AGENT")
        self.assertEqual(response["agent"]["status"], "needs_booking_info")
        self.assertIn("số người", response["message"])
        self.assertIn("thời gian", response["message"])

    def test_agent_creates_booking_after_confirmation(self) -> None:
        customer = self.db.query(User).filter(User.email == "customer-ai-test@what2eat.local").first()
        self.assertIsNotNone(customer)
        session_id = uuid.uuid4()
        session = crud_ai_chat.get_or_create_session(self.db, session_id, customer.user_id, title="agent booking")
        first_response = generate_recommendation("Tìm quán lẩu cho 4 người", self.db, session_id=session_id, limit=3)
        self._log_recommendations(session_id, "Tìm quán lẩu cho 4 người", first_response)

        availability_response = generate_recommendation(
            "đặt quán thứ 1 cho 4 người ngày 21/06/2026 lúc 19h",
            self.db,
            current_user=customer,
            session_id=session_id,
        )
        self.assertEqual(availability_response["source"], "AGENT")
        self.assertEqual(availability_response["agent"]["status"], "awaiting_booking_confirmation")
        self.assertIn("Bạn xác nhận đặt bàn không", availability_response["message"])

        crud_ai_chat.update_session(
            self.db,
            session,
            AIChatSessionUpdate(
                context_summary=f"agent_state={serialize_agent_state(availability_response['agent_state'])}"
            ),
        )
        confirmation_response = generate_recommendation(
            "ok đặt đi",
            self.db,
            current_user=customer,
            session_id=session_id,
        )

        self.assertEqual(confirmation_response["source"], "AGENT")
        self.assertEqual(confirmation_response["agent"]["status"], "booking_created")
        self.assertIsNotNone(confirmation_response["booking"])
        self.assertEqual(confirmation_response["booking"]["guest_count"], 4)
        self.assertIn("Mã booking", confirmation_response["message"])

    def test_agent_modifies_pending_booking_guest_count(self) -> None:
        session_id = uuid.uuid4()
        session = crud_ai_chat.get_or_create_session(self.db, session_id, None, title="agent modify guests")
        restaurant_id = "cccccccc-0000-0000-0000-000000001002"
        crud_ai_chat.update_session(
            self.db,
            session,
            AIChatSessionUpdate(
                context_summary=(
                    "agent_state="
                    + serialize_agent_state(
                        {
                            "pending_action": "confirm_booking",
                            "restaurant_id": restaurant_id,
                            "restaurant_name": "Lẩu Test Một",
                            "guest_count": 4,
                            "reservation_time": "2026-06-21T19:00:00",
                        }
                    )
                )
            ),
        )

        response = generate_recommendation("đổi thành 6 người", self.db, session_id=session_id)

        self.assertEqual(response["source"], "AGENT")
        self.assertEqual(response["agent"]["status"], "awaiting_booking_confirmation")
        self.assertEqual(response["agent_state"]["guest_count"], 6)
        self.assertIn("6 người", response["message"])

    def test_agent_merges_missing_booking_time_from_follow_up(self) -> None:
        session_id = uuid.uuid4()
        session = crud_ai_chat.get_or_create_session(self.db, session_id, None, title="agent add time")
        restaurant_id = "cccccccc-0000-0000-0000-000000001002"
        crud_ai_chat.update_session(
            self.db,
            session,
            AIChatSessionUpdate(
                context_summary=(
                    "agent_state="
                    + serialize_agent_state(
                        {
                            "pending_action": "collect_booking_info",
                            "restaurant_id": restaurant_id,
                            "restaurant_name": "Lẩu Test Một",
                            "guest_count": 4,
                        }
                    )
                )
            ),
        )

        response = generate_recommendation("lúc 20h đi", self.db, session_id=session_id)

        self.assertEqual(response["source"], "AGENT")
        self.assertEqual(response["agent"]["status"], "awaiting_booking_confirmation")
        self.assertEqual(response["agent_state"]["guest_count"], 4)
        self.assertIn("20:00", response["message"])

    def test_agent_cancels_pending_booking(self) -> None:
        session_id = uuid.uuid4()
        session = crud_ai_chat.get_or_create_session(self.db, session_id, None, title="agent cancel")
        crud_ai_chat.update_session(
            self.db,
            session,
            AIChatSessionUpdate(
                context_summary=(
                    "agent_state="
                    + serialize_agent_state(
                        {
                            "pending_action": "confirm_booking",
                            "restaurant_id": "cccccccc-0000-0000-0000-000000001002",
                            "guest_count": 4,
                            "reservation_time": "2026-06-21T19:00:00",
                        }
                    )
                )
            ),
        )

        response = generate_recommendation("thôi không đặt nữa", self.db, session_id=session_id)

        self.assertEqual(response["source"], "AGENT")
        self.assertEqual(response["agent"]["status"], "booking_cancelled")
        self.assertEqual(response["agent_state"], {})
        self.assertIn("hủy", response["message"])

    def _log_recommendations(self, session_id: uuid.UUID, query: str, response: dict) -> None:
        for index, restaurant in enumerate(response["recommended_restaurants"], start=1):
            crud_ai_chat.create_recommendation_log(
                self.db,
                RecommendationLogCreate(
                    session_id=session_id,
                    restaurant_id=uuid.UUID(restaurant["id"]),
                    score=restaurant["match_score"],
                    reason=restaurant["reason"],
                    source=response["source"],
                    rank_position=index,
                    prompt_summary=query,
                ),
            )


def _seed_test_data() -> None:
    owner_id = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
    customer_id = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002")
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
        db.add(
            User(
                user_id=customer_id,
                full_name="Test Customer",
                email="customer-ai-test@what2eat.local",
                password_hash="test",
                role="CUSTOMER",
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
        db.add(
            MenuItem(
                item_id=uuid.uuid4(),
                restaurant_id=uuid.UUID("cccccccc-0000-0000-0000-000000001003"),
                name="Mì trộn sinh viên",
                description="Món mì trộn dễ ăn, phục vụ nhanh.",
                price=30000,
                category="Mì",
                availability_status="AVAILABLE",
            )
        )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    unittest.main()
