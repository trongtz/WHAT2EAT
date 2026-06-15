import apiClient from "./apiClient";
import { invalidateCachePrefix } from "./requestCache";

export const reviewService = {
  create: async (payload) => {
    const response = await apiClient.post("/reviews", {
      restaurant_id: payload.restaurantId,
      rating: Number(payload.rating),
      comment: payload.comment?.trim() || null,
    });
    invalidateCachePrefix("restaurants:list");
    invalidateCachePrefix("restaurants:detail:");
    invalidateCachePrefix("owner:reviews");
    return response.data;
  },

  getMyReviews: async () => {
    const response = await apiClient.get("/reviews/me");
    return response.data;
  },

  getMyReviewsPage: async ({ skip = 0, limit = 20 } = {}) => {
    const response = await apiClient.get("/reviews/me", { params: { skip, limit } });
    return response.data;
  },

  delete: async (reviewId) => {
    await apiClient.delete(`/reviews/${reviewId}`);
    invalidateCachePrefix("restaurants:list");
    invalidateCachePrefix("restaurants:detail:");
    invalidateCachePrefix("owner:reviews");
  },
};
