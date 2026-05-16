import apiClient from "./apiClient";
import { getCachedResource, invalidateCachePrefix } from "./requestCache";
import { normalizeRestaurant } from "./restaurantService";

const FAVORITES_TTL_MS = 2 * 60 * 1000;

const normalizeFavorite = (item) => ({
  ...item,
  id: item.favorite_id ?? item.id,
  favoriteId: item.favorite_id ?? item.id,
  customerId: item.customer_id ?? item.customerId,
  restaurantId: item.restaurant_id ?? item.restaurantId,
  createdAt: item.created_at ?? item.createdAt,
});

const invalidateFavoriteCaches = (restaurantId) => {
  invalidateCachePrefix("favorites:");
  if (restaurantId) {
    invalidateCachePrefix(`favorites:state:${restaurantId}`);
  }
};

export const favoriteService = {
  getFavorites: async () =>
    getCachedResource(
      "favorites:list",
      async () => {
        const response = await apiClient.get("/favorites");
        return response.data.map(normalizeFavorite);
      },
      { ttlMs: FAVORITES_TTL_MS }
    ),

  getFavoriteRestaurantIds: async () => {
    const items = await favoriteService.getFavorites();
    return items.map((item) => String(item.restaurantId));
  },

  getFavoriteRestaurants: async () =>
    getCachedResource(
      "favorites:restaurants",
      async () => {
        const response = await apiClient.get("/favorites/restaurants");
        return response.data.map(normalizeRestaurant);
      },
      { ttlMs: FAVORITES_TTL_MS }
    ),

  isFavorite: async (restaurantId) =>
    getCachedResource(
      `favorites:state:${restaurantId}`,
      async () => {
        const ids = await favoriteService.getFavoriteRestaurantIds();
        return ids.includes(String(restaurantId));
      },
      { ttlMs: FAVORITES_TTL_MS }
    ),

  toggle: async (restaurantId) => {
    const response = await apiClient.post("/favorites/toggle", { restaurant_id: restaurantId });
    invalidateFavoriteCaches(restaurantId);
    return {
      restaurantId: String(response.data.restaurant_id ?? restaurantId),
      isFavorite: Boolean(response.data.is_favorite),
    };
  },

  remove: async (restaurantId) => {
    await apiClient.delete(`/favorites/${restaurantId}`);
    invalidateFavoriteCaches(restaurantId);
  },
};
