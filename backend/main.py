import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.database import Base, engine
from core.init_db import seed_data

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
from api.routes.api import api_router

logger = logging.getLogger(__name__)

app = FastAPI(title="WHAT2EAT API")


@app.on_event("startup")
def initialize_database() -> None:
    try:
        Base.metadata.create_all(bind=engine)
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
