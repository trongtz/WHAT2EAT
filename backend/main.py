import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.config import settings
from core.database import Base, SessionLocal, engine

# Import models so SQLAlchemy can register metadata before startup initialization.
import models.ai_chat
import models.booking
import models.capacity
import models.checkin
import models.customer_profile
import models.dish
import models.favorite
import models.moderation_log
import models.notification
import models.owner_profile
import models.restaurant
import models.restaurant_taxonomy
import models.review
import models.search_history
import models.user
from models.review import Review
from api.routes.api import api_router

logger = logging.getLogger(__name__)

app = FastAPI(title="WHAT2EAT API")

def _ensure_review_uniqueness() -> None:
    if engine.dialect.name != "postgresql":
        return

    inspector = inspect(engine)
    unique_constraints = inspector.get_unique_constraints("reviews")
    if any(constraint.get("name") == "uq_reviews_customer_restaurant" for constraint in unique_constraints):
        return

    with SessionLocal() as db:
        duplicate_groups = (
            db.query(Review.customer_id, Review.restaurant_id)
            .group_by(Review.customer_id, Review.restaurant_id)
            .having(func.count(Review.review_id) > 1)
            .all()
        )

        for customer_id, restaurant_id in duplicate_groups:
            reviews = (
                db.query(Review)
                .filter(Review.customer_id == customer_id, Review.restaurant_id == restaurant_id)
                .order_by(Review.created_at.desc(), Review.review_id.desc())
                .all()
            )
            for review in reviews[1:]:
                db.delete(review)

        db.commit()

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE reviews "
                "ADD CONSTRAINT uq_reviews_customer_restaurant "
                "UNIQUE (customer_id, restaurant_id)"
            )
        )


@app.on_event("startup")
def initialize_database() -> None:
    try:
        if settings.AUTO_CREATE_TABLES:
            Base.metadata.create_all(bind=engine)
        _ensure_review_uniqueness()
        if settings.AUTO_SEED:
            from core.init_db import seed_data

            seed_data()
    except SQLAlchemyError as exc:
        logger.warning("Database initialization skipped: %s", exc)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"message": str(exc.detail)})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"message": "Invalid request data", "details": exc.errors()},
    )


app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "WHAT2EAT Backend is running!"}
