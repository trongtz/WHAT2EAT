from fastapi import APIRouter

from . import admin, ai, ai_sessions, auth, bookings, checkins, dishes, favorites, notifications, owner, profile, restaurants, reviews, search_history, taxonomy

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["Profile"])
api_router.include_router(restaurants.router, prefix="/restaurants", tags=["Restaurants"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Recommendations"])
api_router.include_router(ai_sessions.router, prefix="/ai", tags=["AI Sessions"])
api_router.include_router(owner.router, prefix="/owner", tags=["Owner Dashboard"])
api_router.include_router(dishes.router, prefix="/dishes", tags=["Dishes"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(checkins.router, prefix="/checkins", tags=["Check-ins"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(search_history.router, prefix="/search-history", tags=["Search History"])
api_router.include_router(taxonomy.router, prefix="/taxonomy", tags=["Taxonomy"])
