# AI Recommendation Smoke Test

Chạy từ thư mục repo backend:

```bash
cd "/Users/hvpu/Downloads/what2eat/WHAT2EAT-upstream"
PYTHONPYCACHEPREFIX=/private/tmp/what2eat_pycache python3 backend/scripts/smoke_ai_recommend.py "quán cafe yên tĩnh gần đây dưới 100k" --lat 10.7738 --lng 106.704 --limit 5
```

Ví dụ test prompt có bán kính riêng:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/what2eat_pycache python3 backend/scripts/smoke_ai_recommend.py "lẩu cho nhóm 4 người trong 3km" --lat 10.7738 --lng 106.704 --limit 5
PYTHONPYCACHEPREFIX=/private/tmp/what2eat_pycache python3 backend/scripts/smoke_ai_recommend.py "quán Nhật trong 500m" --lat 10.7738 --lng 106.704 --limit 5
```

Response cần kiểm tra các field chính:

```json
{
  "filters_applied": {
    "radius_km": 2.0
  },
  "recommended_restaurants": [
    {
      "id": "...",
      "name": "...",
      "distance_km": 0.93,
      "match_score": 0.87,
      "available_capacity": 75,
      "quality_score": 0.39,
      "availability_score": 1.0,
      "quality_signals": {
        "rating_avg": 4.8,
        "rating_count": 0,
        "checkin_count_30d": 0,
        "favorite_count": 1,
        "booking_count_30d": 1
      }
    }
  ]
}
```

Ghi chú:

- Khi request có `lat/lng`, backend dùng bán kính mặc định `2km`.
- Nếu prompt có khoảng cách như `500m`, `1.5km`, `3 km`, backend dùng khoảng cách đó.
- Kết quả được lọc theo bán kính trước, sau đó rank theo prompt match, distance, quality và availability.

## Test OpenAI Parser

Gắn key trong file:

```bash
backend/.env
```

Thêm hoặc sửa các dòng:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_INTENT_PARSER=true
```

Sau đó chạy lại smoke test. Nếu parser chạy qua OpenAI, response sẽ có:

```json
{
  "intent": {
    "parser_mode": "openai"
  }
}
```

Nếu OpenAI lỗi, timeout hoặc thiếu key, hệ thống tự fallback về `heuristic`.
