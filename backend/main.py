from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.database import engine, Base

# LƯU Ý: Phải import tất cả các models ở đây để create_all nhận diện được
import models.user
# import models.restaurant
# import models.booking

# CHỈ IMPORT MASTER ROUTER
from api.routes.api import api_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WHAT2EAT API")

# 1. CẤU HÌNH CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. CHUẨN HÓA FORMAT LỖI (Giữ nguyên như cũ)
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"message": str(exc.detail)})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"message": "Dữ liệu đầu vào không hợp lệ", "details": exc.errors()})

# 3. KẾT NỐI ROUTER
# Gắn toàn bộ các API vào đường dẫn gốc /api
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "WHAT2EAT Backend is running!"}