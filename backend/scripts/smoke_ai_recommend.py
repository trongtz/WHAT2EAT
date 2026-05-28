from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from uuid import UUID


BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BACKEND_DIR / ".env"

if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'what2eat.db'}")
os.environ.setdefault("SECRET_KEY", "local-smoke-test-secret")
os.environ.setdefault("OPENAI_API_KEY", "")

import models.registry  # noqa: E402,F401
from core.database import Base, SessionLocal, engine  # noqa: E402
from core.init_db import seed_data  # noqa: E402
from models.user import User  # noqa: E402
from services.ai_service import generate_recommendation  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a local AI recommendation smoke test against backend services."
    )
    parser.add_argument("query", help="Natural-language prompt from the user.")
    parser.add_argument("--lat", type=float, default=None, help="User latitude.")
    parser.add_argument("--lng", type=float, default=None, help="User longitude.")
    parser.add_argument("--limit", type=int, default=5, help="Number of recommendations.")
    parser.add_argument("--session-id", type=UUID, default=None, help="Existing chat session UUID.")
    parser.add_argument("--user-email", default=None, help="Seeded customer email for personalized smoke tests.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    Base.metadata.create_all(bind=engine)
    seed_data()
    db = SessionLocal()
    try:
        current_user = None
        if args.user_email:
            current_user = db.query(User).filter(User.email == args.user_email).first()
            if not current_user:
                raise SystemExit(f"User not found: {args.user_email}")
        response = generate_recommendation(
            args.query,
            db,
            latitude=args.lat,
            longitude=args.lng,
            current_user=current_user,
            session_id=args.session_id,
            limit=args.limit,
        )
        print(json.dumps(response, ensure_ascii=False, indent=2, default=str))
    finally:
        db.close()


if __name__ == "__main__":
    main()
