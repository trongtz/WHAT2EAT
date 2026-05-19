import apiClient from "./apiClient";

export const reviewService = {
  create: async (payload) => {
    const response = await apiClient.post("/reviews", {
      restaurant_id: payload.restaurantId,
      reservation_id: payload.reservationId || null,
      rating: Number(payload.rating),
      comment: payload.comment?.trim() || null,
    });
    return response.data;
  },
};
