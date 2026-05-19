import apiClient from "./apiClient";
import { normalizeRestaurant } from "./restaurantService";

export const aiService = {
  recommend: async (payload) => {
    const query = payload?.query ?? payload?.prompt ?? "";
    const response = await apiClient.post("/ai/recommend", { query });
    const data = response.data || {};

    return {
      message: data.message ?? "",
      restaurants: Array.isArray(data.recommended_restaurants)
        ? data.recommended_restaurants.map(normalizeRestaurant)
        : [],
    };
  },
};
