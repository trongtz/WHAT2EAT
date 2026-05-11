from fastapi import APIRouter

# Import các router con
from api.routes import auth, restaurants, bookings, ai, owner, dishes, favorites
api_router = APIRouter()

# Gom nhóm và gắn tiền tố (prefix) tương ứng
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(restaurants.router, prefix="/restaurants", tags=["Restaurants"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Recommendations"])
api_router.include_router(owner.router, prefix="/owner", tags=["Owner Dashboard"])
api_router.include_router(dishes.router, prefix="/dishes", tags=["Dishes (Thực đơn)"])