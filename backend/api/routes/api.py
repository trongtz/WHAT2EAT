from fastapi import APIRouter

from . import admin, ai, auth, bookings, dishes, favorites, owner, restaurants

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(restaurants.router, prefix="/restaurants", tags=["Restaurants"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Recommendations"])
api_router.include_router(owner.router, prefix="/owner", tags=["Owner"])
api_router.include_router(dishes.router, prefix="/dishes", tags=["Dishes"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
